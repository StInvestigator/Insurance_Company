from django.views.generic import TemplateView
import json
import requests
from urllib.parse import urljoin
import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px


class DatabaseOptimizationDashboardView(TemplateView):
    template_name = 'analytics/db_optimization_dashboard.html'
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx

    def post(self, request, *args, **kwargs):
        num_queries = int(request.POST.get('num_queries', 150))
        num_workers_str = request.POST.get('num_workers', '1,2,4,8,16')
        batch_sizes_str = request.POST.get('batch_sizes', '10,25,50,100')
        what_to_test = 'test_what' in request.POST.get('test_what', 'thread')

        num_workers = [int(x.strip()) for x in num_workers_str.split(',') if x.strip().isdigit()]
        batch_sizes = [int(x.strip()) for x in batch_sizes_str.split(',') if x.strip().isdigit()]

        data = {
            'num_queries': num_queries,
            'num_workers_range': num_workers,
            'batch_sizes': batch_sizes,
            'test_threads': what_to_test == 'thread',
            'test_processes': what_to_test != 'thread'
        }

        api_url = urljoin(request.build_absolute_uri('/'), '/api/analytics/db-optimization/')
        try:
            response = requests.post(api_url, json=data, timeout=300)
            if response.status_code == 200:
                result_data = response.json()
                processed_results = self._process_results(result_data)
                return self.render_to_response(self.get_context_data(
                    results=processed_results,
                    params=data
                ))
            else:
                return self.render_to_response(self.get_context_data(
                    error=f'API returned status {response.status_code}',
                    params=data
                ))
        except Exception as e:
            return self.render_to_response(self.get_context_data(
                error=str(e),
                params=data
            ))

    def _process_results(self, result_data):
        opt = result_data.get('optimal_config', {})
        optimal_config_html = (
            f"<p><strong>Кількість потоків/процесів:</strong> {opt.get('num_workers', 'N/A')}</p>"
            f"<p><strong>Розмір пакету:</strong> {opt.get('batch_size', 'N/A')}</p>"
            f"<p><strong>Тип:</strong> {'Процеси' if opt.get('use_processes') else 'Потоки'}</p>"
            f"<p><strong>Загальний час виконання:</strong> {opt.get('total_time', 0):.3f} секунд</p>"
        )

        avg_time_by_workers = result_data.get('avg_time_by_workers', {})
        workers_sorted = sorted([int(w) for w in avg_time_by_workers.keys()])
        times = [avg_time_by_workers[str(w)] for w in workers_sorted]
        
        # 1. Line Chart
        fig_time = go.Figure()
        fig_time.add_trace(go.Scatter(
            x=workers_sorted,
            y=times,
            mode='lines+markers',
            name='Середній час виконання',
            line={'color': 'blue', 'width': 2},
            marker={'size': 8}
        ))
        fig_time.update_layout(
            title='Залежність часу виконання від кількості потоків/процесів',
            xaxis={'title': 'Кількість потоків/процесів'},
            yaxis={'title': 'Час виконання (секунди)'},
            margin={'t': 40}
        )
        time_chart_html = pio.to_html(fig_time, full_html=False, include_plotlyjs=False)

        all_results = result_data.get('all_results', [])
        all_results.sort(key=lambda r: (r['num_workers'], r['batch_size'], 1 if r['use_processes'] else 0))
        
        workers_set = sorted(list(set(r['num_workers'] for r in all_results)))
        batch_sizes_set = sorted(list(set(r['batch_size'] for r in all_results)))
        
        heatmap_data_map = {}
        for r in all_results:
            key = f"{r['num_workers']}_{r['batch_size']}"
            if key not in heatmap_data_map or heatmap_data_map[key]['total_time'] > r['total_time']:
                heatmap_data_map[key] = r
        
        # 2. Heatmap
        # Подготавливаем данные для plotly.express
        heatmap_data = []
        for bs in batch_sizes_set:
            for w in workers_set:
                key = f"{w}_{bs}"
                val = heatmap_data_map[key]['total_time'] if key in heatmap_data_map else None
                if val is not None:
                    heatmap_data.append({
                        'Workers': str(w),
                        'Batch Size': str(bs),
                        'Execution Time': val
                    })
        
        fig_heatmap = px.density_heatmap(
            heatmap_data,
            x='Workers',
            y='Batch Size',
            z='Execution Time',
            histfunc='avg',
            title='Теплова карта: Час виконання залежно від параметрів',
            labels={'Execution Time': 'Час (сек)', 'Workers': 'Кількість потоків/процесів', 'Batch Size': 'Розмір пакету'},
            color_continuous_scale='Viridis',
            category_orders={
                'Workers': [str(w) for w in workers_set],
                'Batch Size': [str(bs) for bs in batch_sizes_set]
            }
        )
        fig_heatmap.update_layout(margin={'t': 40})
        heatmap_chart_html = pio.to_html(fig_heatmap, full_html=False, include_plotlyjs=False)

        cpu_by_workers = {}
        mem_by_workers = {}
        for r in all_results:
            w = r['num_workers']
            cpu_by_workers.setdefault(w, []).append(r['cpu_usage_percent'])
            mem_by_workers.setdefault(w, []).append(r['memory_usage_mb'])
        
        # 3. CPU Chart
        fig_cpu = go.Figure()
        for w in workers_set:
            avg_cpu = sum(cpu_by_workers[w]) / len(cpu_by_workers[w])
            fig_cpu.add_trace(go.Bar(
                x=[str(w)],
                y=[avg_cpu],
                name=f"{w} потоків/процесів"
            ))
        fig_cpu.update_layout(
            title='Використання CPU',
            xaxis={'title': 'Кількість потоків/процесів'},
            yaxis={'title': 'CPU (%)'},
            margin={'t': 40}
        )
        cpu_chart_html = pio.to_html(fig_cpu, full_html=False, include_plotlyjs=False)

        # 4. Memory Chart
        fig_mem = go.Figure()
        for w in workers_set:
            avg_mem = sum(mem_by_workers[w]) / len(mem_by_workers[w])
            fig_mem.add_trace(go.Bar(
                x=[str(w)],
                y=[avg_mem],
                name=f"{w} потоків/процесів"
            ))
        fig_mem.update_layout(
            title='Використання пам\'яті',
            xaxis={'title': 'Кількість потоків/процесів'},
            yaxis={'title': 'Пам\'ять (MB)'},
            margin={'t': 40}
        )
        mem_chart_html = pio.to_html(fig_mem, full_html=False, include_plotlyjs=False)

        table_rows = []
        for r in all_results:
            row = f"""
            <tr>
                <td>{r['num_workers']}</td>
                <td>{r['batch_size']}</td>
                <td>{'Процеси' if r['use_processes'] else 'Потоки'}</td>
                <td>{r['total_time']:.3f}</td>
                <td>{(r['avg_time_per_query'] * 1000):.2f}</td>
                <td>{r['success_count']}</td>
                <td>{r['error_count']}</td>
                <td>{r['cpu_usage_percent']:.2f}</td>
                <td>{r['memory_usage_mb']:.2f}</td>
            </tr>
            """
            table_rows.append(row)
        table_html = "".join(table_rows)

        return {
            'optimal_config_html': optimal_config_html,
            'time_chart_html': time_chart_html,
            'heatmap_chart_html': heatmap_chart_html,
            'cpu_chart_html': cpu_chart_html,
            'mem_chart_html': mem_chart_html,
            'table_html': table_html,
        }

