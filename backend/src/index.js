const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const repoRoutes = require('./routes/repo');
const agentRoutes = require('./routes/agent');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// Routes
app.use('/api/repo', repoRoutes);
app.use('/api/agent', agentRoutes);

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'GitShepherd Backend' });
});

app.listen(PORT, () => {
  console.log(`GitShepherd backend running on port ${PORT}`);
});
