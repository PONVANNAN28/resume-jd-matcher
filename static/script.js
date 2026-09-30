document.getElementById('uploadBtn').addEventListener('click', async () => {
    const fileInput = document.getElementById('resumeFile');
    const resultsDiv = document.getElementById('results');

    if (fileInput.files.length === 0) {
        resultsDiv.textContent = 'Please choose a PDF file first.';
        return;
    }

    const formData = new FormData();
    formData.append('resume', fileInput.files[0]);

    resultsDiv.innerHTML = '<p class="loading">Analyzing your resume...</p>';

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.error) {
            resultsDiv.innerHTML = `<p class="error">${data.error}</p>`;
            return;
        }

        let html = '';

        html += `<div class="summary">
            <p><strong>Detected skills</strong></p>
            <div class="tag-list">${data.skills.map(s => `<span class="tag">${s}</span>`).join('')}</div>
            <p class="roles-line"><strong>Suggested roles:</strong> ${data.job_titles.join(', ')}</p>
        </div>`;

        html += `<h3 class="jobs-heading">Matching Jobs</h3>`;

        if (data.jobs.length === 0) {
            html += `<p>No matching jobs found right now.</p>`;
        } else {
            html += `<div class="jobs-grid">`;
            data.jobs.forEach(job => {
                html += `
                    <div class="job-card">
                        <div class="job-info">
                            <p class="job-title">${job.title}</p>
                            <p class="job-meta">${job.company} — ${job.location}</p>
                            <p class="job-desc">${job.description}</p>
                        </div>
                        <a href="${job.url}" target="_blank" class="apply-btn">Apply</a>
                    </div>
                `;
            });
            html += `</div>`;
        }

        resultsDiv.innerHTML = html;

    } catch (err) {
        resultsDiv.innerHTML = `<p class="error">Something went wrong: ${err.message}</p>`;
    }
});