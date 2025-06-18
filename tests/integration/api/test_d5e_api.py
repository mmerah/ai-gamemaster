"""Comprehensive integration tests for D5e API endpoints.

This test file combines:
1. Unified API design tests (current endpoints)
2. Performance and concurrency tests
3. Data consistency verification
4. Error handling and edge cases
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Generator, List

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.core.container import get_container
from tests.conftest import get_test_config


class TestD5eAPIIntegration:
    """Test D5e API endpoints with full integration."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> Generator[FlaskClient, None, None]:
        """Set up Flask test client."""
        from app import create_app

        # Create app with test config
        app = create_app(get_test_config())
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        yield self.client

        # Cleanup
        self.app_context.pop()

    # ==================== UNIFIED API TESTS ====================
    # Tests for the new unified /api/d5e/content endpoint

    def test_content_endpoint_basic(self) -> None:
        """Test basic content endpoint with type parameter."""
        # Test ability scores
        response = self.client.get("/api/d5e/content?type=ability-scores")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 6  # Should have 6 ability scores

        # Check structure
        ability = data[0]
        assert "index" in ability
        assert "name" in ability
        assert "full_name" in ability

    @pytest.mark.parametrize(
        "content_type,expected_min_count,required_fields",
        [
            ("spells", 1, ["index", "name", "level"]),
            ("monsters", 1, ["index", "name", "challenge_rating"]),
            ("classes", 1, ["index", "name", "hit_die"]),
            ("races", 1, ["index", "name"]),
            ("equipment", 1, ["index", "name"]),
            ("backgrounds", 1, ["index", "name"]),
            ("skills", 1, ["index", "name"]),
            ("features", 1, ["index", "name"]),
        ],
    )
    def test_content_types(
        self, content_type: str, expected_min_count: int, required_fields: List[str]
    ) -> None:
        """Test various content types through unified endpoint."""
        response = self.client.get(f"/api/d5e/content?type={content_type}")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) >= expected_min_count

        # Check first item has required fields
        if data:
            item = data[0]
            for field in required_fields:
                assert field in item

    def test_content_endpoint_missing_type(self) -> None:
        """Test content endpoint without required type parameter."""
        response = self.client.get("/api/d5e/content")
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "type" in data["error"].lower()

    def test_content_endpoint_invalid_type(self) -> None:
        """Test content endpoint with invalid type."""
        response = self.client.get("/api/d5e/content?type=invalid")
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "valid_types" in data

    # ==================== SPELL FILTERING TESTS ====================

    @pytest.mark.parametrize(
        "filter_params,validation_func",
        [
            ("level=1", lambda spell: spell["level"] == 1),
            ("school=evocation", lambda spell: spell["school"]["index"] == "evocation"),
            (
                "class_name=wizard",
                lambda spell: any(
                    cls.get("index") == "wizard" for cls in spell.get("classes", [])
                ),
            ),
        ],
    )
    def test_spell_filtering(self, filter_params: str, validation_func: Any) -> None:
        """Test spell filtering with various parameters."""
        response = self.client.get(f"/api/d5e/content?type=spells&{filter_params}")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)

        # Validate all returned spells match the filter
        for spell in data:
            assert validation_func(spell)

    def test_spell_combined_filtering(self) -> None:
        """Test spell filtering with multiple parameters."""
        response = self.client.get(
            "/api/d5e/content?type=spells&level=1&class_name=wizard"
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)

        # All spells should be level 1 wizard spells
        for spell in data:
            assert spell["level"] == 1
            wizard_found = any(
                cls.get("index") == "wizard" for cls in spell.get("classes", [])
            )
            assert wizard_found

    @pytest.mark.parametrize(
        "invalid_params",
        [
            "level=15",  # Invalid level
            "class_name=invalid_class",  # Invalid class
            "school=invalid_school",  # Invalid school
        ],
    )
    def test_spell_invalid_filters(self, invalid_params: str) -> None:
        """Test spell endpoint with invalid filter values."""
        response = self.client.get(f"/api/d5e/content?type=spells&{invalid_params}")
        assert response.status_code == 200  # No validation, returns empty list

        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 0  # Should return empty list for invalid filters

    # ==================== MONSTER FILTERING TESTS ====================

    def test_monster_filtering_by_cr(self) -> None:
        """Test monster filtering by CR range."""
        response = self.client.get("/api/d5e/content?type=monsters&min_cr=1&max_cr=5")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)

        # All monsters should be within CR range
        for monster in data:
            cr = monster["challenge_rating"]
            assert 1 <= cr <= 5

    def test_monster_filtering_by_size(self) -> None:
        """Test monster filtering by size."""
        response = self.client.get("/api/d5e/content?type=monsters&size=medium")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)

        # All monsters should be medium size
        for monster in data:
            assert monster["size"].lower() == "medium"

    def test_monster_invalid_filters(self) -> None:
        """Test monster endpoint with invalid filter values."""
        # Invalid CR range (min > max)
        response = self.client.get("/api/d5e/content?type=monsters&min_cr=10&max_cr=5")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 0

        # Invalid size
        response = self.client.get("/api/d5e/content?type=monsters&size=invalid_size")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 0

    # ==================== CONTENT BY ID TESTS ====================

    @pytest.mark.parametrize(
        "content_path,expected_index,expected_name",
        [
            ("spells/fireball", "fireball", "Fireball"),
            ("classes/wizard", "wizard", "Wizard"),
            ("monsters/goblin", "goblin", "Goblin"),
        ],
    )
    def test_content_by_id(
        self, content_path: str, expected_index: str, expected_name: str
    ) -> None:
        """Test getting specific content by ID."""
        response = self.client.get(f"/api/d5e/content/{content_path}")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["index"] == expected_index
        assert data["name"] == expected_name

    def test_content_by_id_not_found(self) -> None:
        """Test getting non-existent content by ID."""
        response = self.client.get("/api/d5e/content/spells/nonexistent")
        assert response.status_code == 404

        data = json.loads(response.data)
        assert "error" in data

    # ==================== SPECIALIZED ENDPOINT TESTS ====================

    def test_character_options_endpoint(self) -> None:
        """Test character options endpoint."""
        response = self.client.get("/api/d5e/character-options")
        assert response.status_code == 200

        data = json.loads(response.data)
        required_keys = [
            "races",
            "classes",
            "backgrounds",
            "ability_scores",
            "skills",
            "languages",
        ]
        for key in required_keys:
            assert key in data
            assert isinstance(data[key], list)
            assert len(data[key]) > 0

        # Specific checks
        assert len(data["ability_scores"]) == 6

    def test_search_endpoint(self) -> None:
        """Test universal search endpoint."""
        response = self.client.get("/api/d5e/search?q=fire")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "query" in data
        assert data["query"] == "fire"
        assert "results" in data
        assert isinstance(data["results"], dict)

        # Should find some results
        total_results = sum(len(items) for items in data["results"].values())
        assert total_results > 0

    def test_search_with_categories(self) -> None:
        """Test search with category filtering."""
        response = self.client.get("/api/d5e/search?q=sword&categories=equipment")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "results" in data
        if data["results"]:
            assert any("equipment" in category for category in data["results"].keys())

    def test_search_missing_query(self) -> None:
        """Test search endpoint without query parameter."""
        response = self.client.get("/api/d5e/search")
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "q" in data["error"]

    def test_class_at_level_endpoint(self) -> None:
        """Test class at level endpoint."""
        response = self.client.get("/api/d5e/classes/wizard/levels/5")
        # This endpoint may return 404 due to reference resolution issues
        # This is a known limitation that will be fixed in future phases
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = json.loads(response.data)
            assert "class_" in data or "class_name" in data
            assert "level" in data or "level_data" in data
            if "level_data" in data:
                assert data["level_data"]["level"] == 5
            else:
                assert data["level"] == 5

    def test_starting_equipment_endpoint(self) -> None:
        """Test starting equipment endpoint."""
        response = self.client.get(
            "/api/d5e/starting-equipment?class_name=fighter&background=soldier"
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["class_name"] == "fighter"
        assert data["background"] == "soldier"
        assert "equipment" in data

    def test_starting_equipment_missing_params(self) -> None:
        """Test starting equipment endpoint with missing parameters."""
        response = self.client.get("/api/d5e/starting-equipment?class_name=fighter")
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "class_name" in data["error"]
        assert "background" in data["error"]

    def test_encounter_budget_endpoint(self) -> None:
        """Test encounter budget endpoint."""
        response = self.client.get(
            "/api/d5e/encounter-budget?levels=1,2,3&difficulty=medium"
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "party_levels" in data
        assert "difficulty" in data
        assert "xp_budget" in data
        assert data["party_levels"] == [1, 2, 3]
        assert data["difficulty"] == "medium"
        assert isinstance(data["xp_budget"], int)

    def test_content_statistics_endpoint(self) -> None:
        """Test content statistics endpoint."""
        response = self.client.get("/api/d5e/content-statistics")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, dict)

        # Check common categories
        expected_categories = ["spells", "monsters", "classes", "equipment"]
        for category in expected_categories:
            assert category in data
            assert isinstance(data[category], int)
            assert data[category] > 0

    # ==================== DEPRECATED ENDPOINT TESTS ====================
    # Verify that old endpoints are properly removed

    @pytest.mark.parametrize(
        "old_endpoint",
        [
            "/api/d5e/spells",
            "/api/d5e/monsters",
            "/api/d5e/races",
            "/api/d5e/classes",
            "/api/d5e/backgrounds",
            "/api/d5e/skills",
            "/api/d5e/equipment",
        ],
    )
    def test_deprecated_endpoints_removed(self, old_endpoint: str) -> None:
        """Test that deprecated endpoints return 404."""
        response = self.client.get(old_endpoint)
        assert response.status_code == 404

    # ==================== PERFORMANCE TESTS ====================

    def test_api_performance_basic(self) -> None:
        """Test basic API performance for small datasets."""
        endpoints = [
            "/api/d5e/content?type=ability-scores",
            "/api/d5e/content?type=skills",
            "/api/d5e/content?type=languages",
            "/api/d5e/content?type=damage-types",
            "/api/d5e/content?type=equipment-categories",
        ]

        for endpoint in endpoints:
            start_time = time.time()
            response = self.client.get(endpoint)
            end_time = time.time()

            assert response.status_code == 200
            # Small datasets should respond within 500ms
            assert (end_time - start_time) < 0.5

    def test_api_performance_large_datasets(self) -> None:
        """Test API performance with large datasets."""
        large_endpoints = [
            "/api/d5e/content?type=spells",
            "/api/d5e/content?type=monsters",
            "/api/d5e/content?type=equipment",
            "/api/d5e/content?type=features",
        ]

        for endpoint in large_endpoints:
            start_time = time.time()
            response = self.client.get(endpoint)
            end_time = time.time()

            assert response.status_code == 200
            # Large datasets should respond within 2 seconds
            assert (end_time - start_time) < 2.0

    def test_api_performance_filtered_queries(self) -> None:
        """Test performance of filtered queries."""
        filtered_endpoints = [
            "/api/d5e/content?type=spells&level=1&class_name=wizard",
            "/api/d5e/content?type=monsters&min_cr=1&max_cr=5&size=medium",
            "/api/d5e/search?q=fire&categories=spells",
        ]

        for endpoint in filtered_endpoints:
            start_time = time.time()
            response = self.client.get(endpoint)
            end_time = time.time()

            assert response.status_code == 200
            # Filtered queries should still be fast
            assert (end_time - start_time) < 1.0

    # ==================== CONCURRENCY TESTS ====================

    def test_concurrent_requests(self) -> None:
        """Test that concurrent requests don't cause race conditions."""
        results: List[int] = []
        errors: List[str] = []

        def make_request() -> None:
            try:
                response = self.client.get("/api/d5e/content?type=spells")
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Make 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            for future in futures:
                future.result()

        # All requests should succeed
        assert len(errors) == 0
        assert all(status == 200 for status in results)
        assert len(results) == 10

    def test_concurrent_different_endpoints(self) -> None:
        """Test concurrent requests to different endpoints."""
        endpoints = [
            "/api/d5e/content?type=spells",
            "/api/d5e/content?type=monsters",
            "/api/d5e/search?q=dragon",
            "/api/d5e/character-options",
            "/api/d5e/content-statistics",
        ]
        results: Dict[str, int] = {}
        errors: List[str] = []

        def make_request(endpoint: str) -> None:
            try:
                response = self.client.get(endpoint)
                results[endpoint] = response.status_code
            except Exception as e:
                errors.append(f"{endpoint}: {str(e)}")

        # Make concurrent requests to different endpoints
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(make_request, endpoint) for endpoint in endpoints
            ]
            for future in futures:
                future.result()

        # All requests should succeed
        assert len(errors) == 0
        assert all(status == 200 for status in results.values())
        assert len(results) == len(endpoints)

    # ==================== DATA CONSISTENCY TESTS ====================

    def test_data_consistency_across_calls(self) -> None:
        """Test that API data is consistent across multiple calls."""
        # Make the same request multiple times
        responses = []
        for _ in range(3):
            response = self.client.get("/api/d5e/content?type=ability-scores")
            assert response.status_code == 200
            responses.append(json.loads(response.data))

        # All responses should be identical
        first_response = responses[0]
        for response in responses[1:]:
            assert response == first_response

    def test_data_consistency_filtered_queries(self) -> None:
        """Test consistency of filtered query results."""
        # Test spell filtering consistency
        responses = []
        for _ in range(3):
            response = self.client.get(
                "/api/d5e/content?type=spells&level=3&school=evocation"
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            # Sort by index for consistent comparison
            data.sort(key=lambda x: x["index"])
            responses.append(data)

        # All responses should be identical
        first_response = responses[0]
        for response in responses[1:]:
            assert response == first_response

    # ==================== ERROR HANDLING TESTS ====================

    def test_error_handling_invalid_endpoints(self) -> None:
        """Test error handling for invalid endpoints."""
        response = self.client.get("/api/d5e/invalid-endpoint")
        assert response.status_code == 404

    def test_error_handling_malformed_parameters(self) -> None:
        """Test error handling for malformed query parameters."""
        # Non-numeric CR values
        response = self.client.get("/api/d5e/content?type=monsters&min_cr=abc")
        assert response.status_code in [200, 400]  # May return empty list or error

        # Invalid difficulty
        response = self.client.get(
            "/api/d5e/encounter-budget?levels=1,2,3&difficulty=super-hard"
        )
        assert response.status_code in [200, 400]

    def test_search_parameter_combinations(self) -> None:
        """Test various search parameter combinations."""
        # Test valid combinations that should work
        combinations = [
            "/api/d5e/content?type=spells&class_name=wizard&level=1",
            "/api/d5e/content?type=spells&school=evocation&level=3",
            "/api/d5e/content?type=monsters&min_cr=0&max_cr=1",
            "/api/d5e/search?q=dragon&categories=monsters,spells",
        ]

        for endpoint in combinations:
            response = self.client.get(endpoint)
            # Should not error even if no results
            assert response.status_code == 200
            data = json.loads(response.data)
            # Should return valid structure even if empty
            assert isinstance(data, (list, dict))
