from django.test import TestCase
from django.contrib.auth.models import User
from backend.models import AnalyzedArea, Road, GreenSpace

class TestModels(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.area = AnalyzedArea.objects.create(
            user=self.user,
            north=50.5,
            south=49.5,
            east=30.5,
            west=29.5,
            area=100,
            road_count=10,
            congestion=50,
            ecology=70,
            pedestrian_friendly=60,
            public_transport=40
        )

    def test_analyzed_area_str(self):
        self.assertEqual(
            str(self.area),
            f"Area {self.area.id}: [{self.area.north}, {self.area.west}] to [{self.area.south}, {self.area.east}]"
        )

    def test_road_creation(self):
        road = Road.objects.create(
            area=self.area,
            osm_id=123,
            name="Test Road",
            road_type="primary",
            length=5.5
        )
        self.assertEqual(str(road), "Test Road (primary)")

    def test_green_space_creation(self):
        space = GreenSpace.objects.create(
            area=self.area,
            osm_id=456,
            name="Test Park",
            space_type="park"
        )
        self.assertEqual(str(space), "Test Park (park)")

    def test_road_type_stats(self):
        from backend.models import RoadTypeStats
        stats = RoadTypeStats.objects.create(
            area=self.area,
            road_type="Головні",
            count=5
        )
        self.assertEqual(str(stats), "Головні: 5")

    def test_hourly_congestion(self):
        from backend.models import HourlyCongestion
        congestion = HourlyCongestion.objects.create(
            area=self.area,
            hour=8,
            congestion_level=75
        )
        self.assertEqual(str(congestion), "Hour 8: 75%")