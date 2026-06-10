document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const jobSelector = document.getElementById('jobSelector');
    const jobDetailsCard = document.getElementById('jobDetailsCard');
    const jobDetailTitle = document.getElementById('jobDetailTitle');
    const jobDetailSkills = document.getElementById('jobDetailSkills');
    const jobDetailEdu = document.getElementById('jobDetailEdu');
    
    const dropZone = document.getElementById('dropZone');
    const resumeFileInput = document.getElementById('resumeFileInput');
    const fileInfoZone = document.getElementById('fileInfoZone');
    const selectedFileName = document.getElementById('selectedFileName');
    const uploadForm = document.getElementById('uploadForm');
    const btnMatchSubmit = document.getElementById('btnMatchSubmit');
    
    const resultsPlaceholder = document.getElementById('resultsPlaceholder');
    const resultsLoader = document.getElementById('resultsLoader');
    const resultsContent = document.getElementById('resultsContent');
    
    const overallScoreRing = document.getElementById('overallScoreRing');
    const overallScoreValue = document.getElementById('overallScoreValue');
    const btnUseBaseModel = document.getElementById('btnUseBaseModel');
    const btnUseTunedModel = document.getElementById('btnUseTunedModel');
    
    const scoreSkills = document.getElementById('scoreSkills');
    const progressSkills = document.getElementById('progressSkills');
    const scoreExperience = document.getElementById('scoreExperience');
    const progressExperience = document.getElementById('progressExperience');
    const expValidityLabel = document.getElementById('expValidityLabel');
    const scoreProjects = document.getElementById('scoreProjects');
    const progressProjects = document.getElementById('progressProjects');
    const scoreEducation = document.getElementById('scoreEducation');
    const progressEducation = document.getElementById('progressEducation');
    
    const skillsCoveragePct = document.getElementById('skillsCoveragePct');
    const countFoundSkills = document.getElementById('countFoundSkills');
    const countMissingSkills = document.getElementById('countMissingSkills');
    const foundSkillsBadges = document.getElementById('foundSkillsBadges');
    const missingSkillsBadges = document.getElementById('missingSkillsBadges');
    
    const groqStatusBadge = document.getElementById('groqStatusBadge');
    const feedbackHave = document.getElementById('feedbackHave');
    const feedbackMissing = document.getElementById('feedbackMissing');
    const feedbackImprove = document.getElementById('feedbackImprove');
    
    const rawResumeSkills = document.getElementById('rawResumeSkills');
    const rawResumeExperience = document.getElementById('rawResumeExperience');
    const rawResumeProjects = document.getElementById('rawResumeProjects');
    const rawResumeEducation = document.getElementById('rawResumeEducation');

    // Global variables to store matching results
    let currentMatchData = null;
    let useTunedModelActive = false;

    // Load available job descriptions
    fetch('/api/jobs')
        .then(response => response.json())
        .then(jobs => {
            jobSelector.innerHTML = '<option value="" selected disabled>Select a position...</option>';
            jobs.forEach(job => {
                const option = document.createElement('option');
                option.value = job.id;
                option.textContent = job.title;
                option.dataset.skills = job.required_skills.join(', ');
                option.dataset.education = job.education_requirements.description;
                option.dataset.title = job.title;
                jobSelector.appendChild(option);
            });
        })
        .catch(err => {
            console.error('Error loading jobs:', err);
            jobSelector.innerHTML = '<option value="" disabled>Error loading jobs</option>';
        });

    // Handle job selection change
    jobSelector.addEventListener('change', () => {
        const selectedOption = jobSelector.options[jobSelector.selectedIndex];
        if (selectedOption && selectedOption.value) {
            jobDetailTitle.textContent = selectedOption.dataset.title;
            jobDetailSkills.textContent = selectedOption.dataset.skills;
            jobDetailEdu.textContent = selectedOption.dataset.education;
            jobDetailsCard.style.display = 'block';
            
            // Add custom micro-animation to card opening
            jobDetailsCard.style.opacity = 0;
            setTimeout(() => {
                jobDetailsCard.style.transition = 'opacity 0.3s ease';
                jobDetailsCard.style.opacity = 1;
            }, 50);
        } else {
            jobDetailsCard.style.display = 'none';
        }
    });

    // Drag and Drop File Handlers
    dropZone.addEventListener('click', () => {
        resumeFileInput.click();
    });

    resumeFileInput.addEventListener('change', () => {
        handleFileSelect(resumeFileInput.files[0]);
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            resumeFileInput.files = e.dataTransfer.files;
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    function handleFileSelect(file) {
        if (file) {
            if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
                selectedFileName.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
                fileInfoZone.style.display = 'block';
            } else {
                alert('Only PDF files are supported.');
                resumeFileInput.value = '';
                fileInfoZone.style.display = 'none';
            }
        }
    }

    // Form Submission
    uploadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const jobId = jobSelector.value;
        const file = resumeFileInput.files[0];
        
        if (!jobId) {
            alert('Please select a target job position first.');
            return;
        }
        
        if (!file) {
            alert('Please upload a resume PDF.');
            return;
        }
        
        // UI Loading State
        resultsPlaceholder.style.display = 'none';
        resultsContent.style.display = 'none';
        resultsLoader.style.display = 'block';
        btnMatchSubmit.disabled = true;
        btnMatchSubmit.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
        
        const formData = new FormData();
        formData.append('resume', file);
        formData.append('job_id', jobId);
        
        fetch('/api/match', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            resultsLoader.style.display = 'none';
            btnMatchSubmit.disabled = false;
            btnMatchSubmit.innerHTML = '<i class="bi bi-lightning-charge-fill me-1"></i> Analyze Match';
            
            if (data.success) {
                currentMatchData = data;
                renderMatchResults();
                resultsContent.style.display = 'block';
            } else {
                resultsPlaceholder.style.display = 'block';
                alert(data.error || 'An error occurred during matching.');
            }
        })
        .catch(err => {
            console.error('Error matching resume:', err);
            resultsLoader.style.display = 'none';
            resultsPlaceholder.style.display = 'block';
            btnMatchSubmit.disabled = false;
            btnMatchSubmit.innerHTML = '<i class="bi bi-lightning-charge-fill me-1"></i> Analyze Match';
            alert('A network error occurred. Please try again.');
        });
    });

    // Toggle base vs fine-tuned model scoring view
    window.toggleModelSelection = function(useTuned) {
        if (useTunedModelActive === useTuned) return;
        useTunedModelActive = useTuned;
        
        if (useTuned) {
            btnUseBaseModel.classList.remove('active');
            btnUseTunedModel.classList.add('active');
            btnUseTunedModel.classList.add('purple');
            // Change theme style of the score ring and progress bars dynamically
            overallScoreRing.style.boxShadow = 'var(--shadow-purple)';
        } else {
            btnUseBaseModel.classList.add('active');
            btnUseTunedModel.classList.remove('active');
            btnUseTunedModel.classList.remove('purple');
            overallScoreRing.style.boxShadow = 'var(--shadow-neon)';
        }
        
        renderMatchResults();
    };

    function renderMatchResults() {
        if (!currentMatchData) return;
        
        const matchData = useTunedModelActive ? currentMatchData.tuned_model_match : currentMatchData.base_model_match;
        const parsedResume = currentMatchData.parsed_resume;
        
        // 1. Overall Score Ring with smooth conic-gradient transition
        const score = matchData.overall_score;
        const scoreDeg = (score / 100) * 360;
        
        // Determine theme colors depending on the active model
        const primaryColor = useTunedModelActive ? 'var(--accent-purple)' : 'var(--accent-cyan)';
        
        overallScoreRing.style.background = `conic-gradient(${primaryColor} ${scoreDeg}deg, rgba(255, 255, 255, 0.08) 0deg)`;
        
        // Animate counter
        animateCounter(overallScoreValue, parseFloat(overallScoreValue.textContent) || 0, score, 800);
        
        // 2. Category Breakdown Scores
        const breakdown = matchData.breakdown;
        
        // Set values
        scoreSkills.textContent = `${breakdown.skills.score}%`;
        progressSkills.style.width = `${breakdown.skills.score}%`;
        
        scoreExperience.textContent = `${breakdown.experience.score}%`;
        progressExperience.style.width = `${breakdown.experience.score}%`;
        
        // Setup experience validity display
        if (breakdown.experience.is_valid) {
            expValidityLabel.textContent = breakdown.experience.display;
            expValidityLabel.className = "small mt-1 text-end text-success";
        } else {
            expValidityLabel.textContent = breakdown.experience.display;
            expValidityLabel.className = "small mt-1 text-end text-danger";
        }
        
        scoreProjects.textContent = `${breakdown.projects.score}%`;
        progressProjects.style.width = `${breakdown.projects.score}%`;
        
        scoreEducation.textContent = `${breakdown.education.score}%`;
        progressEducation.style.width = `${breakdown.education.score}%`;
        
        // Color classes based on model type
        const barClass = useTunedModelActive ? 'progress-bar-purple' : 'progress-bar-cyan';
        const otherBarClass = useTunedModelActive ? 'progress-bar-cyan' : 'progress-bar-purple';
        
        [progressSkills, progressExperience, progressProjects, progressEducation].forEach(bar => {
            bar.classList.remove(otherBarClass);
            bar.classList.add(barClass);
        });

        // 3. ATS Skill Coverage Tab
        skillsCoveragePct.textContent = `${breakdown.skills.coverage_percentage}%`;
        countFoundSkills.textContent = breakdown.skills.found_skills.length;
        countMissingSkills.textContent = breakdown.skills.missing_skills.length;
        
        foundSkillsBadges.innerHTML = '';
        if (breakdown.skills.found_skills.length > 0) {
            breakdown.skills.found_skills.forEach(skill => {
                const badge = document.createElement('span');
                badge.className = 'skill-badge matched';
                badge.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i> ${skill}`;
                foundSkillsBadges.appendChild(badge);
            });
        } else {
            foundSkillsBadges.innerHTML = '<p class="text-secondary small italic">No matching skills found.</p>';
        }
        
        missingSkillsBadges.innerHTML = '';
        if (breakdown.skills.missing_skills.length > 0) {
            breakdown.skills.missing_skills.forEach(skill => {
                const badge = document.createElement('span');
                badge.className = 'skill-badge missing';
                badge.innerHTML = `<i class="bi bi-x-circle-fill me-1"></i> ${skill}`;
                missingSkillsBadges.appendChild(badge);
            });
        } else {
            missingSkillsBadges.innerHTML = '<p class="text-success small"><i class="bi bi-check-circle-fill me-1"></i> Zero missing required skills!</p>';
        }

        // 4. AI Feedback Tab
        const explanation = currentMatchData.explanation;
        const hasGroqKey = currentMatchData.has_groq_key;
        const isLiveGroq = currentMatchData.is_live_groq;
        
        // Update Groq Status Badge
        if (isLiveGroq) {
            groqStatusBadge.textContent = 'Live Groq (Llama 3)';
            groqStatusBadge.className = 'badge bg-success text-white';
        } else {
            groqStatusBadge.textContent = hasGroqKey ? 'Fallback Analysis' : 'Local Rule-based Analysis';
            groqStatusBadge.className = 'badge bg-secondary text-light';
        }
        
        // Helper to render lists
        renderFeedbackList(feedbackHave, explanation.have);
        renderFeedbackList(feedbackMissing, explanation.missing);
        renderFeedbackList(feedbackImprove, explanation.improve);

        // 5. Parsed Sections Tab
        rawResumeSkills.innerHTML = formatParsedText(parsedResume.skills || 'Not provided / extracted');
        rawResumeExperience.innerHTML = formatParsedText(parsedResume.experience || 'Not provided / extracted');
        rawResumeProjects.innerHTML = formatParsedText(parsedResume.projects || 'Not provided / extracted');
        rawResumeEducation.innerHTML = formatParsedText(parsedResume.education || 'Not provided / extracted');
    }

    function renderFeedbackList(container, items) {
        container.innerHTML = '';
        if (items && items.length > 0) {
            items.forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                container.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'No detailed points provided.';
            container.appendChild(li);
        }
    }

    function formatParsedText(text) {
        if (!text) return 'None';
        return text.replace(/\n/g, '<br>');
    }

    function animateCounter(element, start, end, duration) {
        let startTime = null;
        const step = (timestamp) => {
            if (!startTime) startTime = timestamp;
            const progress = Math.min((timestamp - startTime) / duration, 1);
            const value = start + progress * (end - start);
            element.textContent = value.toFixed(1);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                element.textContent = end.toFixed(1);
            }
        };
        window.requestAnimationFrame(step);
    }
});
