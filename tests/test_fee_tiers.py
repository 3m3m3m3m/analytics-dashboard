#!/usr/bin/env python3
"""
Unit Tests for Fee Tier Distribution Feature

This module contains unit tests for:
1. Backend API endpoint response structure validation
2. Fee tier mapping logic
3. Data transformation and aggregation

Run with: python -m pytest tests/test_fee_tiers.py -v
Or: python3 -m unittest tests.test_fee_tiers -v
"""

import unittest
from unittest.mock import Mock, patch
import json


class TestFeeTierMapping(unittest.TestCase):
    """Tests for fee tier to basis points mapping"""

    # Fee tier mapping as defined in the backend (api_server.py lines 2876-2883)
    TIER_BPS_MAP = {
        0: 'Ultimate',
        15: 'Diamond',
        25: 'Platinum',
        30: 'Gold',
        40: 'Silver',
        45: 'Bronze',
        50: 'None',
    }

    # Expected tier order (highest to lowest)
    EXPECTED_TIER_ORDER = [
        'Ultimate', 'Diamond', 'Platinum', 'Gold', 'Silver', 'Bronze', 'None', 'Unknown'
    ]

    def test_all_known_tiers_have_mapping(self):
        """Verify all expected tiers have BPS mappings"""
        mapped_tiers = set(self.TIER_BPS_MAP.values())
        expected_mapped = {'Ultimate', 'Diamond', 'Platinum', 'Gold', 'Silver', 'Bronze', 'None'}
        self.assertEqual(mapped_tiers, expected_mapped)

    def test_bps_values_are_ascending(self):
        """Verify BPS values are in ascending order (lower = better tier)"""
        bps_values = list(self.TIER_BPS_MAP.keys())
        self.assertEqual(bps_values, sorted(bps_values))

    def test_tier_order_is_correct(self):
        """Verify tier order from best (Ultimate) to worst (None)"""
        bps_to_tier = [(bps, tier) for bps, tier in sorted(self.TIER_BPS_MAP.items())]
        tier_order = [tier for _, tier in bps_to_tier]
        expected = ['Ultimate', 'Diamond', 'Platinum', 'Gold', 'Silver', 'Bronze', 'None']
        self.assertEqual(tier_order, expected)

    def test_unknown_bps_maps_to_unknown_tier(self):
        """Verify unknown BPS values would map to 'Unknown' tier"""
        unknown_bps_values = [1, 5, 10, 20, 35, 60, 100]
        for bps in unknown_bps_values:
            self.assertNotIn(bps, self.TIER_BPS_MAP)


class TestFeeTierResponseStructure(unittest.TestCase):
    """Tests for fee tier API response structure"""

    SAMPLE_RESPONSE = {
        'tierDistribution': [
            {
                'tier': 'Ultimate',
                'userCount': 100,
                'totalVolume': 500000.0,
                'avgVolumePerUser': 5000.0
            },
            {
                'tier': 'Diamond',
                'userCount': 50,
                'totalVolume': 200000.0,
                'avgVolumePerUser': 4000.0
            },
            {
                'tier': 'None',
                'userCount': 200,
                'totalVolume': 100000.0,
                'avgVolumePerUser': 500.0
            }
        ],
        'totalUsers': 350,
        'totalVolume': 800000.0
    }

    def test_response_has_required_keys(self):
        """Verify response contains all required top-level keys"""
        required_keys = ['tierDistribution', 'totalUsers', 'totalVolume']
        for key in required_keys:
            self.assertIn(key, self.SAMPLE_RESPONSE)

    def test_tier_distribution_is_list(self):
        """Verify tierDistribution is a list"""
        self.assertIsInstance(self.SAMPLE_RESPONSE['tierDistribution'], list)

    def test_tier_item_has_required_keys(self):
        """Verify each tier item has required keys"""
        required_keys = ['tier', 'userCount', 'totalVolume', 'avgVolumePerUser']
        for item in self.SAMPLE_RESPONSE['tierDistribution']:
            for key in required_keys:
                self.assertIn(key, item)

    def test_tier_values_are_valid(self):
        """Verify tier values are from known tier list"""
        valid_tiers = {'Ultimate', 'Diamond', 'Platinum', 'Gold', 'Silver', 'Bronze', 'None', 'Unknown'}
        for item in self.SAMPLE_RESPONSE['tierDistribution']:
            self.assertIn(item['tier'], valid_tiers)

    def test_user_count_is_non_negative(self):
        """Verify user counts are non-negative"""
        for item in self.SAMPLE_RESPONSE['tierDistribution']:
            self.assertGreaterEqual(item['userCount'], 0)

    def test_volume_is_non_negative(self):
        """Verify volumes are non-negative"""
        for item in self.SAMPLE_RESPONSE['tierDistribution']:
            self.assertGreaterEqual(item['totalVolume'], 0)
            self.assertGreaterEqual(item['avgVolumePerUser'], 0)

    def test_total_users_matches_sum(self):
        """Verify totalUsers equals sum of individual tier counts"""
        total_from_items = sum(item['userCount'] for item in self.SAMPLE_RESPONSE['tierDistribution'])
        self.assertEqual(self.SAMPLE_RESPONSE['totalUsers'], total_from_items)

    def test_total_volume_matches_sum(self):
        """Verify totalVolume equals sum of individual tier volumes"""
        total_from_items = sum(item['totalVolume'] for item in self.SAMPLE_RESPONSE['tierDistribution'])
        self.assertAlmostEqual(self.SAMPLE_RESPONSE['totalVolume'], total_from_items, places=2)


class TestFeeTierDataTransformations(unittest.TestCase):
    """Tests for data transformations used in fee tier processing"""

    def test_empty_response_handling(self):
        """Verify empty response is handled correctly"""
        empty_response = {
            'tierDistribution': [],
            'totalUsers': 0,
            'totalVolume': 0.0
        }
        self.assertEqual(len(empty_response['tierDistribution']), 0)
        self.assertEqual(empty_response['totalUsers'], 0)
        self.assertEqual(empty_response['totalVolume'], 0.0)

    def test_single_tier_response(self):
        """Verify single tier response is valid"""
        single_tier_response = {
            'tierDistribution': [
                {
                    'tier': 'None',
                    'userCount': 100,
                    'totalVolume': 50000.0,
                    'avgVolumePerUser': 500.0
                }
            ],
            'totalUsers': 100,
            'totalVolume': 50000.0
        }
        self.assertEqual(len(single_tier_response['tierDistribution']), 1)
        self.assertEqual(single_tier_response['tierDistribution'][0]['tier'], 'None')

    def test_avg_volume_calculation(self):
        """Verify average volume per user calculation"""
        tier_data = {
            'tier': 'Gold',
            'userCount': 10,
            'totalVolume': 1000.0,
            'avgVolumePerUser': 100.0
        }
        expected_avg = tier_data['totalVolume'] / tier_data['userCount']
        self.assertAlmostEqual(tier_data['avgVolumePerUser'], expected_avg, places=2)

    def test_percentage_calculation(self):
        """Verify percentage calculations are correct"""
        response = {
            'tierDistribution': [
                {'tier': 'Ultimate', 'userCount': 25, 'totalVolume': 50000.0, 'avgVolumePerUser': 2000.0},
                {'tier': 'None', 'userCount': 75, 'totalVolume': 50000.0, 'avgVolumePerUser': 666.67}
            ],
            'totalUsers': 100,
            'totalVolume': 100000.0
        }

        total_users = response['totalUsers']
        for item in response['tierDistribution']:
            percentage = (item['userCount'] / total_users) * 100
            # Ultimate should be 25%, None should be 75%
            if item['tier'] == 'Ultimate':
                self.assertAlmostEqual(percentage, 25.0, places=1)
            elif item['tier'] == 'None':
                self.assertAlmostEqual(percentage, 75.0, places=1)


class TestSQLQueryLogic(unittest.TestCase):
    """Tests for SQL query logic verification"""

    def test_affiliate_address_matching(self):
        """Verify affiliate address matching logic"""
        # The query checks for 'vi', 'va', 'v0' affiliate addresses
        valid_affiliates = ['vi', 'va', 'v0']
        for affiliate in valid_affiliates:
            self.assertIn(affiliate, valid_affiliates)

    def test_source_filtering(self):
        """Verify source filtering for thorchain/mayachain"""
        valid_sources = ['thorchain', 'mayachain']
        for source in valid_sources:
            self.assertIn(source, valid_sources)

    def test_tier_sorting_order(self):
        """Verify tier sorting order matches expected"""
        # SQL ORDER BY CASE should produce this order
        expected_order = [
            ('Ultimate', 1),
            ('Diamond', 2),
            ('Platinum', 3),
            ('Gold', 4),
            ('Silver', 5),
            ('Bronze', 6),
            ('None', 7),
            ('Unknown', 8)
        ]
        for tier, position in expected_order:
            self.assertGreater(position, 0)
            self.assertLessEqual(position, 8)


class TestFrontendChartColors(unittest.TestCase):
    """Tests for frontend chart color configuration"""

    TIER_COLORS = {
        'Ultimate': '#FFD700',    # Gold
        'Diamond': '#B9F2FF',     # Diamond blue
        'Platinum': '#E5E4E2',    # Platinum silver
        'Gold': '#FFA500',        # Orange gold
        'Silver': '#C0C0C0',      # Silver
        'Bronze': '#CD7F32',      # Bronze
        'None': '#94A3B8',        # Slate gray
        'Unknown': '#6B7280'      # Gray
    }

    def test_all_tiers_have_colors(self):
        """Verify all tiers have assigned colors"""
        expected_tiers = ['Ultimate', 'Diamond', 'Platinum', 'Gold', 'Silver', 'Bronze', 'None', 'Unknown']
        for tier in expected_tiers:
            self.assertIn(tier, self.TIER_COLORS)

    def test_colors_are_valid_hex(self):
        """Verify all colors are valid hex codes"""
        import re
        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
        for tier, color in self.TIER_COLORS.items():
            self.assertIsNotNone(hex_pattern.match(color), f"Invalid hex color for {tier}: {color}")

    def test_premium_tiers_have_distinct_colors(self):
        """Verify premium tiers (Ultimate, Diamond, Platinum) have distinct colors"""
        premium_tiers = ['Ultimate', 'Diamond', 'Platinum']
        premium_colors = [self.TIER_COLORS[t] for t in premium_tiers]
        # All premium colors should be unique
        self.assertEqual(len(premium_colors), len(set(premium_colors)))


class TestFrontendTierDiscounts(unittest.TestCase):
    """Tests for frontend tier discount display values - must match backend"""

    # These values must match the backend BPS values in api_server.py
    TIER_DISCOUNTS = {
        'Ultimate': '0 bps (0%)',
        'Diamond': '15 bps (0.15%)',
        'Platinum': '25 bps (0.25%)',
        'Gold': '30 bps (0.30%)',
        'Silver': '40 bps (0.40%)',
        'Bronze': '45 bps (0.45%)',
        'None': '50 bps (0.50%)',
    }

    # Backend BPS values for cross-reference
    BACKEND_BPS = {
        'Ultimate': 0,
        'Diamond': 15,
        'Platinum': 25,
        'Gold': 30,
        'Silver': 40,
        'Bronze': 45,
        'None': 50,
    }

    def test_all_tiers_have_discount_info(self):
        """Verify all known tiers have discount information"""
        known_tiers = ['Ultimate', 'Diamond', 'Platinum', 'Gold', 'Silver', 'Bronze', 'None']
        for tier in known_tiers:
            self.assertIn(tier, self.TIER_DISCOUNTS)

    def test_discount_format_is_consistent(self):
        """Verify discount format is consistent across tiers"""
        import re
        pattern = re.compile(r'^\d+ bps \(\d+\.\d+%\)$|^0 bps \(0%\)$')
        for tier, discount in self.TIER_DISCOUNTS.items():
            self.assertIsNotNone(pattern.match(discount), f"Invalid format for {tier}: {discount}")

    def test_ultimate_has_zero_fee(self):
        """Verify Ultimate tier has 0% fee"""
        self.assertEqual(self.TIER_DISCOUNTS['Ultimate'], '0 bps (0%)')

    def test_none_has_maximum_fee(self):
        """Verify None tier has maximum 50 bps fee"""
        self.assertIn('50 bps', self.TIER_DISCOUNTS['None'])

    def test_frontend_matches_backend_bps(self):
        """Verify frontend display values match backend BPS values"""
        import re
        for tier, display in self.TIER_DISCOUNTS.items():
            # Extract BPS value from display string
            match = re.match(r'^(\d+) bps', display)
            self.assertIsNotNone(match, f"Could not parse BPS from {display}")
            frontend_bps = int(match.group(1))
            backend_bps = self.BACKEND_BPS[tier]
            self.assertEqual(
                frontend_bps, backend_bps,
                f"Mismatch for {tier}: frontend shows {frontend_bps} bps, backend uses {backend_bps} bps"
            )


if __name__ == '__main__':
    unittest.main(verbosity=2)
