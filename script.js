// Function to add a new rice entry
function addRice(username, title, mediaUrl, mediaType, redditUrl, upvotes, comments) {
    const grid = document.getElementById('riceGrid');
    const riceCard = document.createElement('div');
    riceCard.className = 'rice-card';
    
    let mediaHTML = '';
    if (mediaType === 'video') {
        mediaHTML = `<video class="rice-video" controls><source src="${mediaUrl}" type="video/mp4">Your browser does not support the video tag.</video>`;
    } else if (Array.isArray(mediaUrl)) {
        // Gallery of images
        mediaHTML = `<div class="gallery">`;
        mediaUrl.forEach(url => {
            mediaHTML += `<img src="${url}" alt="Screenshot" class="rice-image">`;
        });
        mediaHTML += `</div>`;
    } else {
        // Single image
        mediaHTML = `<img src="${mediaUrl}" alt="Desktop Screenshot" class="rice-image">`;
    }
    
    riceCard.innerHTML = `
        <div class="rice-header">
            <div class="username">u/${username}</div>
            <div class="rice-title">${title}</div>
        </div>
        <div class="media-container">
            ${mediaHTML}
        </div>
        <a href="${redditUrl}" class="post-link" target="_blank">View on Reddit →</a>
        <div class="stats">
            <span>↑ ${upvotes}</span>
            <span>💬 ${comments}</span>
        </div>
    `;
    
    grid.appendChild(riceCard);
}

// Function to submit a rice for review
function submitRice() {
    const urlInput = document.getElementById('redditUrl');
    const submitBtn = document.getElementById('submitBtn');
    const url = urlInput.value.trim();
    
    // Basic URL validation
    if (!url) {
        alert('Please enter a Reddit URL');
        return;
    }
    
    if (!url.includes('reddit.com/r/unixporn')) {
        alert('Please enter a valid r/unixporn post URL');
        return;
    }
    
    // Disable button during submission
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';
    
    // Create GitHub issue (this would typically call your backend/GitHub API)
    createGitHubIssue(url)
        .then(() => {
            alert('Rice submitted successfully! It will be reviewed and added if approved.');
            urlInput.value = '';
        })
        .catch((error) => {
            alert('Error submitting rice: ' + error.message);
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Rice';
        });
}

// Function to create GitHub issue (placeholder - would need actual implementation)
async function createGitHubIssue(redditUrl) {
    // This is a placeholder function. In a real implementation, you would:
    // 1. Call your backend API or GitHub API directly
    // 2. Create an issue with the Reddit URL
    // 3. This would trigger your GitHub Action workflow
    
    // For now, you could replace this with a call to GitHub's API:
    // const response = await fetch('https://api.github.com/repos/yourusername/yourrepo/issues', {
    //     method: 'POST',
    //     headers: {
    //         'Authorization': 'token YOUR_GITHUB_TOKEN',
    //         'Content-Type': 'application/json',
    //     },
    //     body: JSON.stringify({
    //         title: 'New Rice Submission',
    //         body: `Reddit URL: ${redditUrl}`,
    //         labels: ['rice-submission']
    //     })
    // });
    
    // Simulate API call
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            // Simulate success/failure
            if (Math.random() > 0.1) {
                resolve();
            } else {
                reject(new Error('Network error'));
            }
        }, 1000);
    });
}

// Allow Enter key to submit
document.getElementById('redditUrl').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        submitRice();
    }
});
