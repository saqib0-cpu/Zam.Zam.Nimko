// Chart initialization for all pages
document.addEventListener('DOMContentLoaded', function() {
    // Data Flow Chart
    const flowChartCanvas = document.getElementById('flowChart');
    if (flowChartCanvas) {
        const ctx = flowChartCanvas.getContext('2d');
        const flowChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Vitamin C', 'Protein Powder', 'Hand Sanitizer', 'Multivitamin'],
                datasets: [{
                    label: 'Incoming',
                    data: [50, 30, 100, 40],
                    backgroundColor: 'rgba(67, 97, 238, 0.7)',
                    borderColor: 'rgba(67, 97, 238, 1)',
                    borderWidth: 1
                }, {
                    label: 'Outgoing',
                    data: [12, 8, 25, 15],
                    backgroundColor: 'rgba(247, 37, 133, 0.7)',
                    borderColor: 'rgba(247, 37, 133, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Quantity'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Products'
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Product Flow - Last 7 Days'
                    }
                }
            }
        });
    }

    // Monthly Statement Chart
    const monthlyChartCanvas = document.getElementById('monthlyChart');
    if (monthlyChartCanvas) {
        const ctx = monthlyChartCanvas.getContext('2d');
        const monthlyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                datasets: [{
                    label: 'Revenue',
                    data: [850, 1120, 980, 1408],
                    borderColor: 'rgba(67, 97, 238, 1)',
                    backgroundColor: 'rgba(67, 97, 238, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Profit',
                    data: [380, 520, 420, 571],
                    borderColor: 'rgba(76, 201, 240, 1)',
                    backgroundColor: 'rgba(76, 201, 240, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Amount ($)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Monthly Performance - June 2023'
                    }
                }
            }
        });
    }

    // Profit/Loss Chart
    const profitChartCanvas = document.getElementById('profitChart');
    if (profitChartCanvas) {
        const ctx = profitChartCanvas.getContext('2d');
        const profitChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Vitamin C Tablets', 'Protein Powder', 'Hand Sanitizer', 'Other Products'],
                datasets: [{
                    data: [202, 280, 162, 1248],
                    backgroundColor: [
                        'rgba(67, 97, 238, 0.8)',
                        'rgba(247, 37, 133, 0.8)',
                        'rgba(76, 201, 240, 0.8)',
                        'rgba(67, 97, 238, 0.4)'
                    ],
                    borderColor: [
                        'rgba(67, 97, 238, 1)',
                        'rgba(247, 37, 133, 1)',
                        'rgba(76, 201, 240, 1)',
                        'rgba(67, 97, 238, 0.6)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                    },
                    title: {
                        display: true,
                        text: 'Profit Distribution'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: $${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Filter functionality for data flow page
    const applyFilterBtn = document.getElementById('applyFilter');
    if (applyFilterBtn) {
        applyFilterBtn.addEventListener('click', function() {
            const dateFrom = document.getElementById('dateFrom').value;
            const dateTo = document.getElementById('dateTo').value;
            const productFilter = document.getElementById('productFilter').value;
            
            // Show loading state
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Applying...';
            this.disabled = true;
            
            // Simulate API call
            setTimeout(() => {
                showNotification('Filters applied successfully!', 'success');
                this.innerHTML = 'Apply Filter';
                this.disabled = false;
            }, 1000);
        });
    }
});

// Export functionality
function exportToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const row = [], cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            // Clean and escape data
            let data = cols[j].innerText.replace(/(\r\n|\n|\r)/gm, '').replace(/(\s\s)/gm, ' ');
            data = data.replace(/"/g, '""');
            row.push('"' + data + '"');
        }
        
        csv.push(row.join(','));
    }
    
    // Download CSV file
    const csvFile = new Blob([csv.join('\n')], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
    
    showNotification('Data exported successfully!', 'success');
}

// Print functionality
function printTable(tableId) {
    const table = document.getElementById(tableId);
    const win = window.open('', '', 'height=700,width=700');
    win.document.write('<html><head>');
    win.document.write('<title>Print</title>');
    win.document.write('</head><body>');
    win.document.write(table.outerHTML);
    win.document.write('</body></html>');
    win.document.close();
    win.print();
}