const express = require('express');
const router = express.Router();
const fs = require('fs-extra');
const path = require('path');
const axios = require('axios');
const AdmZip = require('adm-zip');

const WORKSPACE_DIR = path.join(__dirname, '../../workspace');

// Fetch public repo via GitHub tarball
router.post('/fetch', async (req, res) => {
    const { repoUrl } = req.body;

    if (!repoUrl) {
        return res.status(400).json({ error: 'GitHub Repo URL is required' });
    }

    try {
        // Basic URL parsing to get owner/repo
        const parts = repoUrl.replace('https://github.com/', '').split('/');
        if (parts.length < 2) throw new Error('Invalid GitHub URL');

        const owner = parts[0];
        const repo = parts[1].split('#')[0].split('?')[0]; // handle branches or queries

        console.log(`Fetching repo: ${owner}/${repo}`);

        // Ensure workspace exists
        await fs.ensureDir(WORKSPACE_DIR);
        const sessionDir = path.join(WORKSPACE_DIR, `${Date.now()}-${repo}`);
        await fs.ensureDir(sessionDir);

        // Download tarball (faster than git clone for public repos)
        const tarballUrl = `https://api.github.com/repos/${owner}/${repo}/zipball/main`;
        const response = await axios({
            method: 'get',
            url: tarballUrl,
            responseType: 'arraybuffer'
        });

        const zip = new AdmZip(Buffer.from(response.data));
        zip.extractAllTo(sessionDir, true);

        // The zip usually contains a single folder with name like owner-repo-hash
        const folders = await fs.readdir(sessionDir);
        const mainFolder = path.join(sessionDir, folders[0]);

        res.json({
            message: 'Repo fetched successfully',
            owner,
            repo,
            path: mainFolder,
            sessionId: path.basename(sessionDir)
        });

    } catch (error) {
        console.error('Fetch error:', error);
        res.status(500).json({ error: 'Failed to fetch repository: ' + error.message });
    }
});

module.exports = router;
