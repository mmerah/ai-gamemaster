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
from flask.testing import FlaskClient

from tests.conftest import get_test_settings


class TestD5eAPIIntegration:
    """Test D5e API endpoints with full integration."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> Generator[FlaskClient, None, None]:
        """Set up Flask test client."""
        from app import create_app

        # Create app with test config
        app = create_app(get_test_settings())
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

    # ==================== SPECIALIZED ENDPOINT TESTS ====================

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
            "/api/d5e/content?type=spells&school=evocation",
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
            "/api/d5e/content?type=classes",
            "/api/d5e/content?type=equipment",
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

        # Invalid spell level
        response = self.client.get("/api/d5e/content?type=spells&level=999")
        assert response.status_code in [200, 400]

    def test_search_parameter_combinations(self) -> None:
        """Test various search parameter combinations."""
        # Test valid combinations that should work
        combinations = [
            "/api/d5e/content?type=spells&class_name=wizard&level=1",
            "/api/d5e/content?type=spells&school=evocation&level=3",
            "/api/d5e/content?type=monsters&min_cr=0&max_cr=1",
        ]

        for endpoint in combinations:
            response = self.client.get(endpoint)
            # Should not error even if no results
            assert response.status_code == 200
            data = json.loads(response.data)
            # Should return valid structure even if empty
            assert isinstance(data, (list, dict))
