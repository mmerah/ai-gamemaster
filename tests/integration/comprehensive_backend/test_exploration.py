"""
EXPLORATION AND SKILL CHECK TEST

Tests exploration scenarios with skill challenges:
- Trap detection with Perception checks
- Group skill challenges (crossing hazards)
- Different skill types (Perception, Athletics)
- Skill check DC mechanics
- Success and failure handling
- Narrative progression based on skill results

This test ensures non-combat gameplay mechanics work correctly.
"""
import pytest
import uuid
from app.ai_services.schemas import AIResponse
from app.game.unified_models import DiceRequest
from app.events.game_update_events import (
    PlayerDiceRequestAddedEvent,
    NarrativeAddedEvent
)
from .conftest import (
    setup_mock_ai_service_patching,
    verify_event_system_integrity,
    verify_required_event_types
)


def test_exploration_with_skill_checks(app, client, mock_ai_service, event_recorder, container, basic_party, golden_test):
    """Test exploration scenario with skill challenges and trap detection."""
    
    # Set up the mock AI service
    app.config['AI_SERVICE'] = mock_ai_service
    
    # Patch the _get_ai_service method on all event handlers to ensure they use our mock
    ai_service_patchers = setup_mock_ai_service_patching(container, mock_ai_service)
    
    # Clear any initial events
    event_recorder.clear()
    
    try:
        # Player searches for traps
        mock_ai_service.add_response(AIResponse(
            narrative="You carefully examine the corridor. Make a Perception check!",
            reasoning="Trap detection",
            dice_requests=[
                DiceRequest(
                    request_id=str(uuid.uuid4()),
                    character_ids=["fighter"],  # Fighter is searching
                    type="skill_check",
                    dice_formula="1d20+1",  # +1 WIS mod
                    reason="Perception check for traps",
                    skill="perception",
                    dc=15
                )
            ]
        ))
        
        # Player action
        response = client.post("/api/player_action", json={
            "action_type": "free_text",
            "value": "I search the corridor for traps."
        })
        assert response.status_code == 200
        
        # AI reveals trap (add before submitting roll)
        mock_ai_service.add_response(AIResponse(
            narrative="Your keen eyes spot a pressure plate in the floor! You've found a dart trap.",
            reasoning="Trap found"
        ))
        
        # Submit perception roll that triggers the AIResponse revealing the trap
        response = client.post("/api/submit_rolls", json=[{
            "character_id": "fighter",
            "roll_type": "skill_check",
            "dice_formula": "1d20+1",
            "dice_notation": "1d20+1",
            "dice_results": [(20, 16)],
            "total": 17  # Success!
        }])
        assert response.status_code == 200
        
        # ========== PHASE 2: Group Skill Challenge ==========
        
        mock_ai_service.add_response(AIResponse(
            narrative="Further ahead, you encounter a chasm. Everyone must make an Athletics check to cross safely!",
            reasoning="Group skill challenge",
            dice_requests=[
                DiceRequest(
                    request_id=str(uuid.uuid4()),
                    character_ids=["wizard", "fighter"],
                    type="skill_check",
                    dice_formula="1d20",
                    reason="Athletics check to cross chasm",
                    skill="athletics",
                    dc=12
                )
            ]
        ))
        
        response = client.post("/api/player_action", json={
            "action_type": "free_text",
            "value": "We carefully cross the chasm."
        })
        assert response.status_code == 200
        
        # AI processes results (add before submitting rolls)
        mock_ai_service.add_response(AIResponse(
            narrative="Torvin makes it across easily, but Elara slips! Torvin catches her arm just in time.",
            reasoning="Mixed success on group challenge"
        ))
        
        # Submit athletics checks - combine both rolls in a single submission
        client.post("/api/submit_rolls", json=[{
            "character_id": "wizard",
            "roll_type": "skill_check",
            "dice_formula": "1d20",
            "dice_notation": "1d20",
            "dice_results": [(20, 8)],
            "total": 8  # Barely fails
        }, {
            "character_id": "fighter",
            "roll_type": "skill_check",
            "dice_formula": "1d20",
            "dice_notation": "1d20",
            "dice_results": [(20, 15)],
            "total": 15  # Success
        }])
        
        # ========== VERIFICATION ==========
        
        # Verify events
        dice_requests = event_recorder.get_events_of_type(PlayerDiceRequestAddedEvent)
        skill_checks = [e for e in dice_requests if e.roll_type == "skill_check"]
        assert len(skill_checks) >= 2
        
        # Verify different skills were tested
        skills_tested = set(e.skill for e in skill_checks if e.skill)
        assert "perception" in skills_tested
        assert "athletics" in skills_tested
        
        narrative_events = event_recorder.get_events_of_type(NarrativeAddedEvent)
        assert any("trap" in e.content.lower() for e in narrative_events)
        assert any("chasm" in e.content.lower() for e in narrative_events)
    
        # ========== COMPREHENSIVE EVENT VERIFICATION ==========
        
        # Verify event system integrity  
        event_stats = verify_event_system_integrity(event_recorder)
        verify_required_event_types(event_stats['event_types'], "Exploration")
        
        # Test golden file comparison
        golden_test(event_recorder, "exploration")
    
        print(f"✅ EXPLORATION TEST COMPLETE")
        print(f"   📊 Total Events: {event_stats['total_events']}")
        print(f"   🎲 Skills Tested: {len(skills_tested)}")
        print(f"   📝 Event Types: {sorted(event_stats['event_types'])}")
        
    finally:
        # Stop all AI service patchers
        for patcher in ai_service_patchers:
            patcher.stop()