import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from typing import List, Dict


class RoadNetworkVisualizer:
    def __init__(self):
        self.colors = {
            'background': '#f5f5f5',
            'roads': {
                'motorway': '#4a90e2',
                'trunk': '#4a90e2',
                'primary': '#ffa500',
                'secondary': '#ffff00',
                'tertiary': '#ffffff',
                'residential': '#ffffff',
                'service': '#f0f0f0',
            },
            'green_spaces': '#90EE90',
            'parks': '#228B22',
            'water': '#87CEEB',
            'buildings': '#D3D3D3',
        }

    def visualize_network_comparison(self, original_analysis: Dict, improved_plan: Dict, output_path: str = None):
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        self._plot_realistic_map(original_analysis, axes[0, 0], "Поточний стан території")
        self._plot_improved_map(improved_plan, axes[0, 1], "Покращений план території")

        self._plot_metrics_comparison(original_analysis, improved_plan, axes[1, 0])
        self._plot_simple_improvements(improved_plan, axes[1, 1])

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')

        return fig

    def _plot_realistic_map(self, analysis: Dict, ax, title: str):
        bounds = analysis.get('bounds', [[50.45, 30.52], [50.44, 30.53]])
        nw_lat, nw_lng = bounds[0]
        se_lat, se_lng = bounds[1]

        ax.set_xlim(nw_lng, se_lng)
        ax.set_ylim(se_lat, nw_lat)
        ax.set_facecolor(self.colors['background'])

        roads_data = analysis.get('roads_data', [])
        for road in roads_data:
            if 'coordinates' in road and len(road['coordinates']) > 1:
                coords = road['coordinates']
                lats = [coord[0] for coord in coords]
                lngs = [coord[1] for coord in coords]

                highway_type = road.get('highway', 'residential')
                color = self.colors['roads'].get(highway_type, '#ffffff')
                width = self._get_realistic_width(highway_type)

                ax.plot(lngs, lats, color=color, linewidth=width, solid_capstyle='round')

                ax.plot(lngs, lats, color='#666666', linewidth=width + 0.5, zorder=-1)

        green_spaces = analysis.get('green_spaces_data', [])
        for space in green_spaces:
            if 'coordinates' in space and len(space['coordinates']) > 2:
                coords = space['coordinates']
                lats = [coord[0] for coord in coords]
                lngs = [coord[1] for coord in coords]

                space_type = space.get('leisure', 'park')
                color = self.colors['parks'] if space_type == 'park' else self.colors['green_spaces']

                polygon = patches.Polygon(list(zip(lngs, lats)), facecolor=color,
                                          edgecolor='#006400', linewidth=1)
                ax.add_patch(polygon)

        buildings_data = analysis.get('buildings_data', [])
        for building in buildings_data[:20]:  # обмежуємо кількість для швидкості
            if 'coordinates' in building and len(building['coordinates']) > 2:
                coords = building['coordinates']
                lats = [coord[0] for coord in coords]
                lngs = [coord[1] for coord in coords]

                polygon = patches.Polygon(list(zip(lngs, lats)),
                                          facecolor=self.colors['buildings'],
                                          edgecolor='#A9A9A9', linewidth=0.5)
                ax.add_patch(polygon)

        transport_stops = analysis.get('public_transport_stops', [])
        for stop in transport_stops[:10]:
            if 'coordinates' in stop:
                lat, lng = stop['coordinates']
                ax.scatter(lng, lat, c='#FF4500', s=40, marker='s', edgecolor='black', linewidth=1)

        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Довгота')
        ax.set_ylabel('Широта')
        ax.grid(True, alpha=0.3, color='gray', linewidth=0.5)

    def _plot_improved_map(self, improved_plan: Dict, ax, title: str):
        bounds = improved_plan.get('bounds', [[50.45, 30.52], [50.44, 30.53]])
        nw_lat, nw_lng = bounds[0]
        se_lat, se_lng = bounds[1]

        ax.set_xlim(nw_lng, se_lng)
        ax.set_ylim(se_lat, nw_lat)
        ax.set_facecolor(self.colors['background'])

        new_roads = improved_plan.get('roads', [])
        for road in new_roads:
            if 'coordinates' in road and len(road['coordinates']) > 1:
                coords = road['coordinates']
                lats = [coord[0] for coord in coords]
                lngs = [coord[1] for coord in coords]

                road_type = road.get('type', 'residential')
                color = self.colors['roads'].get(road_type, '#ffffff')
                width = self._get_realistic_width(road_type) * 1.2

                if len(lats) > 2:
                    t_orig = np.linspace(0, 1, len(lats))
                    t_smooth = np.linspace(0, 1, len(lats) * 3)

                    lats_smooth = np.interp(t_smooth, t_orig, lats)
                    lngs_smooth = np.interp(t_smooth, t_orig, lngs)

                    ax.plot(lngs_smooth, lats_smooth, color=color, linewidth=width, solid_capstyle='round')
                    ax.plot(lngs_smooth, lats_smooth, color='#333333', linewidth=width + 0.8, zorder=-1)
                else:
                    ax.plot(lngs, lats, color=color, linewidth=width, solid_capstyle='round')
                    ax.plot(lngs, lats, color='#333333', linewidth=width + 0.8, zorder=-1)

        green_spaces = improved_plan.get('green_spaces', [])
        for space in green_spaces:
            if 'coordinates' in space and len(space['coordinates']) > 2:
                coords = space['coordinates']
                lats = [coord[0] for coord in coords]
                lngs = [coord[1] for coord in coords]

                space_type = space.get('type', 'park')
                color = self.colors['parks'] if space_type == 'park' else self.colors['green_spaces']

                polygon = patches.Polygon(list(zip(lngs, lats)),
                                          facecolor=color, edgecolor='#004d00',
                                          linewidth=2, alpha=0.8)
                ax.add_patch(polygon)

        transport_stops = improved_plan.get('transport_stops', [])
        for stop in transport_stops:
            if 'coordinates' in stop:
                lat, lng = stop['coordinates']
                ax.scatter(lng, lat, c='#FF0000', s=80, marker='o',
                           edgecolor='white', linewidth=3, zorder=10)

        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Довгота')
        ax.set_ylabel('Широта')
        ax.grid(True, alpha=0.3, color='gray', linewidth=0.5)

    def _plot_metrics_comparison(self, original: Dict, improved: Dict, ax):
        metrics = ['congestion', 'ecology', 'pedestrian_friendly', 'public_transport']
        metric_names = ['Затори\n(менше = краще)', 'Екологія', 'Пішохідність', 'Транспорт']

        original_values = [original.get(metric, 50) for metric in metrics]
        improved_values = [improved.get(metric, 50) for metric in metrics]

        original_values[0] = 100 - original_values[0]
        improved_values[0] = 100 - improved_values[0]

        x = np.arange(len(metrics))
        width = 0.35

        bars1 = ax.bar(x - width / 2, original_values, width, label='До покращення',
                       color='#ff7f7f', edgecolor='black', linewidth=1)
        bars2 = ax.bar(x + width / 2, improved_values, width, label='Після покращення',
                       color='#90EE90', edgecolor='black', linewidth=1)

        for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
            height1 = bar1.get_height()
            height2 = bar2.get_height()

            ax.text(bar1.get_x() + bar1.get_width() / 2, height1 + 1,
                    f'{height1:.0f}%', ha='center', va='bottom', fontweight='bold')
            ax.text(bar2.get_x() + bar2.get_width() / 2, height2 + 1,
                    f'{height2:.0f}%', ha='center', va='bottom', fontweight='bold')

        ax.set_xlabel('Показники')
        ax.set_ylabel('Оцінка (%)')
        ax.set_title('Порівняння ключових показників', fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(metric_names)
        ax.legend()
        ax.set_ylim(0, 110)
        ax.grid(True, alpha=0.3, axis='y')

    def _plot_simple_improvements(self, improved_plan: Dict, ax):
        improvements = {
            'Нові дороги': len(improved_plan.get('roads', [])),
            'Зелені зони': len(improved_plan.get('green_spaces', [])),
            'Зупинки': len(improved_plan.get('transport_stops', []))
        }

        improvements = {k: v for k, v in improvements.items() if v > 0}

        if improvements:
            categories = list(improvements.keys())
            values = list(improvements.values())
            colors = ['#4a90e2', '#90EE90', '#FF4500'][:len(categories)]

            bars = ax.bar(categories, values, color=colors, edgecolor='black', linewidth=1)

            for bar, value in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                        str(value), ha='center', va='bottom', fontweight='bold')

            ax.set_title('Кількість нових об\'єктів', fontweight='bold')
            ax.set_ylabel('Кількість')
            ax.grid(True, alpha=0.3, axis='y')
        else:
            ax.text(0.5, 0.5, 'Покращення\nне потребують\nнових об\'єктів',
                    ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title('Аналіз покращень', fontweight='bold')

    def _get_realistic_width(self, road_type: str) -> float:
        widths = {
            'motorway': 5.0,
            'trunk': 4.0,
            'primary': 3.5,
            'secondary': 2.5,
            'tertiary': 2.0,
            'residential': 1.5,
            'service': 1.0
        }
        return widths.get(road_type, 1.5)

    def generate_network_svg(self, improved_plan: Dict, output_path: str):
        bounds = improved_plan.get('bounds', [[50.45, 30.52], [50.44, 30.53]])
        nw_lat, nw_lng = bounds[0]
        se_lat, se_lng = bounds[1]

        svg_width = 1000
        svg_height = 800

        def coord_to_svg(lat, lng):
            x = (lng - nw_lng) / (se_lng - nw_lng) * svg_width
            y = (nw_lat - lat) / (nw_lat - se_lat) * svg_height
            return x, y

        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}">
  <rect width="{svg_width}" height="{svg_height}" fill="{self.colors['background']}"/>
  <text x="{svg_width // 2}" y="50" text-anchor="middle" font-size="24" font-weight="bold">
    Покращений план території
  </text>
'''

        green_spaces = improved_plan.get('green_spaces', [])
        for space in green_spaces:
            if 'coordinates' in space and len(space['coordinates']) > 2:
                points = []
                for coord in space['coordinates']:
                    if len(coord) >= 2:
                        x, y = coord_to_svg(coord[0], coord[1])
                        points.append(f"{x},{y}")

                if points:
                    svg_content += f'  <polygon points="{" ".join(points)}" fill="{self.colors["parks"]}" stroke="#004d00" stroke-width="2" opacity="0.8"/>\n'

        roads = improved_plan.get('roads', [])
        for road in roads:
            if 'coordinates' in road and len(road['coordinates']) > 1:
                points = []
                for coord in road['coordinates']:
                    if len(coord) >= 2:
                        x, y = coord_to_svg(coord[0], coord[1])
                        points.append(f"{x},{y}")

                if points:
                    road_type = road.get('type', 'residential')
                    color = self.colors['roads'].get(road_type, '#ffffff')
                    width = self._get_realistic_width(road_type) * 2

                    path_d = f"M {points[0]} " + " L ".join(points[1:])
                    svg_content += f'  <path d="{path_d}" stroke="{color}" stroke-width="{width}" fill="none" stroke-linecap="round"/>\n'

        transport_stops = improved_plan.get('transport_stops', [])
        for stop in transport_stops:
            if 'coordinates' in stop:
                x, y = coord_to_svg(stop['coordinates'][0], stop['coordinates'][1])
                svg_content += f'  <circle cx="{x}" cy="{y}" r="8" fill="#FF0000" stroke="white" stroke-width="3"/>\n'

        svg_content += '</svg>'

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            print(f"SVG збережено: {output_path}")
        except Exception as e:
            print(f"Помилка збереження SVG: {e}")