#!/usr/bin/env python3
"""
Quick Dashboard Server - View your data without Grafana
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os

class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_dashboard_html().encode())
        elif self.path == '/api/sales':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            with open('sales_dashboard_data.json', 'r') as f:
                self.wfile.write(f.read().encode())
        elif self.path == '/api/etl':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            with open('etl_dashboard_data.json', 'r') as f:
                self.wfile.write(f.read().encode())
        else:
            super().do_GET()
    
    def get_dashboard_html(self):
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unilever Data Pipeline - Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: white;
            margin-bottom: 30px;
            text-align: center;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .dashboard-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            justify-content: center;
        }
        .tab-btn {
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            background: white;
            color: #667eea;
            cursor: pointer;
            font-size: 1.1em;
            font-weight: 600;
            transition: all 0.3s;
        }
        .tab-btn.active {
            background: #667eea;
            color: white;
            transform: scale(1.05);
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s;
        }
        .card:hover {
            transform: translateY(-5px);
        }
        .card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .card .value {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
            word-break: break-word;
        }
        .card .unit {
            color: #999;
            font-size: 0.8em;
            margin-top: 5px;
        }
        .chart-container {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .chart-container h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.3em;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        table th {
            background: #f5f5f5;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #ddd;
        }
        table td {
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }
        table tr:hover {
            background: #f9f9f9;
        }
        .status-success {
            color: #4caf50;
            font-weight: bold;
        }
        .status-failed {
            color: #f44336;
            font-weight: bold;
        }
        .full-width {
            grid-column: 1 / -1;
        }
        #canvas-area {
            position: relative;
            height: 300px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Unilever Data Pipeline Dashboard</h1>
        
        <div class="dashboard-tabs">
            <button class="tab-btn active" onclick="switchTab('sales')">💰 Sales Analytics</button>
            <button class="tab-btn" onclick="switchTab('etl')">⚙️ ETL Monitoring</button>
        </div>
        
        <!-- SALES ANALYTICS TAB -->
        <div id="sales" class="tab-content active">
            <div class="grid">
                <div class="card">
                    <h3>Total Revenue</h3>
                    <div class="value" id="sales-revenue">-</div>
                    <div class="unit">USD</div>
                </div>
                <div class="card">
                    <h3>Total Transactions</h3>
                    <div class="value" id="sales-transactions">-</div>
                    <div class="unit">Orders</div>
                </div>
                <div class="card">
                    <h3>Average Order Value</h3>
                    <div class="value" id="sales-avg">-</div>
                    <div class="unit">USD</div>
                </div>
            </div>
            
            <div class="chart-container full-width">
                <h2>Top 10 Products</h2>
                <table id="products-table">
                    <thead>
                        <tr>
                            <th>Product Name</th>
                            <th>Quantity Sold</th>
                            <th>Revenue</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
            
            <div class="chart-container full-width">
                <h2>Top 5 Customers</h2>
                <table id="customers-table">
                    <thead>
                        <tr>
                            <th>Customer Name</th>
                            <th>Transactions</th>
                            <th>Revenue</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>
        
        <!-- ETL MONITORING TAB -->
        <div id="etl" class="tab-content">
            <div class="grid">
                <div class="card">
                    <h3>Total ETL Runs</h3>
                    <div class="value" id="etl-runs">-</div>
                    <div class="unit">All Time</div>
                </div>
                <div class="card">
                    <h3>Total Records Loaded</h3>
                    <div class="value" id="etl-records">-</div>
                    <div class="unit">Records</div>
                </div>
                <div class="card">
                    <h3>Failed Runs (30d)</h3>
                    <div class="value" id="etl-failed">-</div>
                    <div class="unit">Failures</div>
                </div>
                <div class="card">
                    <h3>Quality Issues (30d)</h3>
                    <div class="value" id="etl-issues">-</div>
                    <div class="unit">Issues</div>
                </div>
            </div>
            
            <div class="chart-container full-width">
                <h2>Recent ETL Runs (Last 10)</h2>
                <table id="etl-table">
                    <thead>
                        <tr>
                            <th>Run ID</th>
                            <th>Timestamp</th>
                            <th>Status</th>
                            <th>Records Processed</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        function switchTab(tab) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tab).classList.add('active');
            event.target.classList.add('active');
        }

        function formatCurrency(value) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(value);
        }

        function formatNumber(value) {
            return new Intl.NumberFormat('en-US').format(value);
        }

        async function loadSalesData() {
            try {
                const response = await fetch('/api/sales');
                const data = await response.json();
                
                document.getElementById('sales-revenue').textContent = formatCurrency(data.total_revenue);
                document.getElementById('sales-transactions').textContent = formatNumber(data.transaction_count);
                document.getElementById('sales-avg').textContent = formatCurrency(data.avg_order_value);
                
                // Products table
                const productsBody = document.querySelector('#products-table tbody');
                productsBody.innerHTML = data.top_products.map(p => `
                    <tr>
                        <td>${p.product}</td>
                        <td>${formatNumber(p.quantity)}</td>
                        <td>${formatCurrency(p.revenue)}</td>
                    </tr>
                `).join('');
                
                // Customers table
                const customersBody = document.querySelector('#customers-table tbody');
                customersBody.innerHTML = data.top_customers.map(c => `
                    <tr>
                        <td>${c.customer}</td>
                        <td>${formatNumber(c.transactions)}</td>
                        <td>${formatCurrency(c.revenue)}</td>
                    </tr>
                `).join('');
            } catch (error) {
                console.error('Error loading sales data:', error);
            }
        }

        async function loadETLData() {
            try {
                const response = await fetch('/api/etl');
                const data = await response.json();
                
                document.getElementById('etl-runs').textContent = formatNumber(data.total_runs);
                document.getElementById('etl-records').textContent = formatNumber(data.total_records_loaded);
                document.getElementById('etl-failed').textContent = formatNumber(data.failed_runs_30d);
                document.getElementById('etl-issues').textContent = formatNumber(data.quality_issues_30d);
                
                // Recent runs table
                const etlBody = document.querySelector('#etl-table tbody');
                etlBody.innerHTML = data.recent_runs.map(r => `
                    <tr>
                        <td>#${r.run_id}</td>
                        <td>${r.time}</td>
                        <td><span class="status-success">${r.status.toUpperCase()}</span></td>
                        <td>${formatNumber(r.records)}</td>
                    </tr>
                `).join('');
            } catch (error) {
                console.error('Error loading ETL data:', error);
            }
        }

        // Load data on page load
        window.onload = () => {
            loadSalesData();
            loadETLData();
        };
    </script>
</body>
</html>
        '''

if __name__ == '__main__':
    PORT = 8888
    handler = DashboardHandler
    httpd = HTTPServer(('localhost', PORT), handler)
    
    print(f"\n{'='*80}")
    print(f"📊 DASHBOARD SERVER RUNNING")
    print(f"{'='*80}")
    print(f"\n🌐 Open your browser and go to:")
    print(f"\n   👉 http://localhost:{PORT}")
    print(f"\n📈 You will see:")
    print(f"   • Sales Analytics with top products and customers")
    print(f"   • ETL Monitoring with pipeline health")
    print(f"\nPress Ctrl+C to stop the server\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
        httpd.server_close()
