/**
 * StudySync Dashboard Client-Side Scripts
 * Handles dynamic Chart.js rendering, FullCalendar triggers, modal bindings,
 * and mobile navigation toggles.
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Initialize Bootstrap Tooltips & Popovers
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 2. Mobile Sidebar Toggle
    const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    const sidebar = document.querySelector('.sidebar');
    if (sidebarToggleBtn && sidebar) {
        sidebarToggleBtn.addEventListener('click', function () {
            sidebar.classList.toggle('show');
        });
    }

    // 3. Topbar Search Input Handler
    const topSearchInput = document.getElementById('topSearchInput');
    if (topSearchInput) {
        topSearchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const term = encodeURIComponent(this.value.trim());
                if (term) {
                    window.location.href = `/tasks/search?q=${term}`;
                }
            }
        });
    }

    // 4. Auto-dismiss Flash Alerts after 5 seconds
    const flashAlerts = document.querySelectorAll('.alert-dismissible');
    flashAlerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 6000);
    });

    // 5. Dashboard Charts initialization via API
    initDashboardCharts();
});

/**
 * Fetches dashboard chart statistics from server API and instantiates Chart.js graphs.
 */
function initDashboardCharts() {
    const statusChartCanvas = document.getElementById('taskStatusChart');
    const subjectChartCanvas = document.getElementById('subjectWorkloadChart');

    if (!statusChartCanvas && !subjectChartCanvas) {
        return;
    }

    fetch('/api/dashboard/charts')
        .then(response => response.json())
        .then(data => {
            // A. Status Doughnut Chart
            if (statusChartCanvas) {
                new Chart(statusChartCanvas, {
                    type: 'doughnut',
                    data: {
                        labels: data.status_labels,
                        datasets: [{
                            data: data.status_values,
                            backgroundColor: [
                                '#F59E0B', // Pending - Amber
                                '#6366F1', // In Progress - Indigo
                                '#10B981', // Completed - Emerald
                                '#EF4444'  // Overdue - Red
                            ],
                            borderWidth: 2,
                            borderColor: '#FFFFFF'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    boxWidth: 12,
                                    padding: 15,
                                    font: { family: 'Inter', size: 12 }
                                }
                            }
                        },
                        cutout: '72%'
                    }
                });
            }

            // B. Subject Workload Bar Chart
            if (subjectChartCanvas && data.subject_labels.length > 0) {
                new Chart(subjectChartCanvas, {
                    type: 'bar',
                    data: {
                        labels: data.subject_labels,
                        datasets: [{
                            label: 'Tasks',
                            data: data.subject_values,
                            backgroundColor: data.subject_colors || '#2563EB',
                            borderRadius: 6,
                            maxBarThickness: 32
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: { stepSize: 1, font: { family: 'Inter' } },
                                grid: { color: '#F1F5F9' }
                            },
                            x: {
                                grid: { display: false },
                                ticks: { font: { family: 'Inter', weight: '500' } }
                            }
                        }
                    }
                });
            }
        })
        .catch(err => {
            console.error('Failed to load chart metrics:', err);
        });
}

/**
 * Task Details Modal Populator
 */
function openTaskModal(title, subject, type, dueDate, dueTime, priority, reason, status, description, editUrl) {
    document.getElementById('modalTaskTitle').textContent = title;
    document.getElementById('modalTaskSubject').textContent = subject;
    document.getElementById('modalTaskType').textContent = type;
    document.getElementById('modalTaskDue').textContent = `${dueDate} at ${dueTime}`;
    document.getElementById('modalTaskPriority').textContent = priority;
    document.getElementById('modalTaskReason').textContent = reason || 'Standard scheduling';
    document.getElementById('modalTaskStatus').textContent = status;
    document.getElementById('modalTaskDesc').textContent = description || 'No additional instructions provided.';
    
    const editBtn = document.getElementById('modalTaskEditBtn');
    if (editBtn && editUrl) {
        editBtn.href = editUrl;
    }

    const modal = new bootstrap.Modal(document.getElementById('taskDetailModal'));
    modal.show();
}
