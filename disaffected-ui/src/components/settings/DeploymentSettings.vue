<template>
  <v-card class="pa-6">
    <h3 class="text-h6 mb-2 d-flex align-center">
      <v-icon left class="mr-2">mdi-cloud-upload</v-icon>
      Celery Worker Deployment
    </h3>
    <p class="text-body-2 mb-6 text-medium-emphasis">
      Deploy distributed Celery workers to remote Linux servers for asynchronous task processing (FFmpeg, script compilation, quote extraction, etc.)
    </p>

    <!-- Documentation Section -->
    <v-expansion-panels variant="accordion" class="mb-6">
      <v-expansion-panel>
        <v-expansion-panel-title class="text-subtitle-1 font-weight-medium">
          <v-icon left class="mr-2">mdi-book-open-variant</v-icon>
          System Architecture & How It Works
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <v-card variant="outlined" class="pa-4 mb-4">
            <h4 class="text-subtitle-2 mb-3">Distributed Processing Architecture</h4>

            <div class="mb-4">
              <pre class="text-caption bg-grey-lighten-4 pa-3 rounded" style="overflow-x: auto;">
+---------------+         +-----------------+         +---------------+
|   WHISPER     |  tasks  |   FARMHOUSE     |  poll   |    WORKER     |
|  (FastAPI)    | ------&gt; |    (Redis)      | &lt;------ |   (Celery)    |
|  :8888        |         |    :6379        |         |   FFmpeg      |
+---------------+         +-----------------+         +---------------+
      |                          |                         |
      | 1. Upload video          | 2. Queue task          | 3. Process
      |    Return task_id        |    (BLPOP media)       |    - Extract audio
      |                          |                         |    - Gen thumbnail
      | 4. Poll status           |                         |    - Trim video
      |    GET /tasks/{id}       | 5. Store result        |
      +------------------------------+-------------------------+
              </pre>
            </div>

            <v-alert type="info" variant="tonal" density="compact" class="mb-3">
              <strong>Key Concept:</strong> Show-Build server (whisper) submits tasks to a message queue (Redis on farmhouse).
              Remote workers (kairo, proxima, etc.) poll the queue and execute tasks. Results are stored in Redis and retrieved by polling.
            </v-alert>

            <h4 class="text-subtitle-2 mb-2">Component Roles</h4>
            <v-table density="compact" class="mb-4">
              <thead>
                <tr>
                  <th>Machine</th>
                  <th>Role</th>
                  <th>Services</th>
                  <th>Purpose</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><code>whisper</code></td>
                  <td>Server</td>
                  <td>FastAPI, Celery Client</td>
                  <td>Submits tasks, provides API</td>
                </tr>
                <tr>
                  <td><code>farmhouse</code></td>
                  <td>Broker</td>
                  <td>Redis 7</td>
                  <td>Message queue, result storage</td>
                </tr>
                <tr>
                  <td><code>kairo/proxima</code></td>
                  <td>Worker</td>
                  <td>Celery Worker, FFmpeg</td>
                  <td>Executes heavy tasks</td>
                </tr>
              </tbody>
            </v-table>

            <h4 class="text-subtitle-2 mb-2">Task Queues</h4>
            <v-chip-group>
              <v-chip color="primary" prepend-icon="mdi-video">media</v-chip>
              <v-chip color="secondary" prepend-icon="mdi-file-document">compilation</v-chip>
              <v-chip color="success" prepend-icon="mdi-format-quote-close">quotes</v-chip>
              <v-chip color="info" prepend-icon="mdi-folder-star">assets</v-chip>
            </v-chip-group>
            <p class="text-caption mt-2 text-medium-emphasis">
              Each queue can be processed by dedicated workers for optimal resource allocation
            </p>
          </v-card>

          <v-card variant="outlined" class="pa-4 mb-4">
            <h4 class="text-subtitle-2 mb-3">Deployment Flow</h4>
            <v-timeline density="compact" side="end" class="mb-0">
              <v-timeline-item dot-color="primary" size="small">
                <strong>Step 1:</strong> Configure Redis broker (farmhouse)
                <div class="text-caption text-medium-emphasis">Install Redis 7, set password, enable persistence</div>
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                <strong>Step 2:</strong> Prepare remote server
                <div class="text-caption text-medium-emphasis">Install Docker, mount shared volumes, configure SSH</div>
              </v-timeline-item>
              <v-timeline-item dot-color="primary" size="small">
                <strong>Step 3:</strong> Deploy worker
                <div class="text-caption text-medium-emphasis">Run deployment script or use form below to generate files</div>
              </v-timeline-item>
              <v-timeline-item dot-color="success" size="small">
                <strong>Step 4:</strong> Verify registration
                <div class="text-caption text-medium-emphasis">Worker appears in active workers list</div>
              </v-timeline-item>
            </v-timeline>
          </v-card>

          <v-card variant="outlined" class="pa-4">
            <h4 class="text-subtitle-2 mb-3">Prerequisites</h4>
            <v-list density="compact">
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="success">mdi-check-circle</v-icon>
                </template>
                <v-list-item-title>Redis broker running and accessible (farmhouse:6379)</v-list-item-title>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="success">mdi-check-circle</v-icon>
                </template>
                <v-list-item-title>SSH key-based authentication to remote server</v-list-item-title>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="success">mdi-check-circle</v-icon>
                </template>
                <v-list-item-title>Docker and Docker Compose installed on remote server</v-list-item-title>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="success">mdi-check-circle</v-icon>
                </template>
                <v-list-item-title>Shared volumes mounted: /mnt/sync/disaffected/episodes, /mnt/sync/shared_media</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card>
        </v-expansion-panel-text>
      </v-expansion-panel>

      <v-expansion-panel>
        <v-expansion-panel-title class="text-subtitle-1 font-weight-medium">
          <v-icon left class="mr-2">mdi-server-network</v-icon>
          Current Deployments
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <v-alert type="info" variant="tonal" class="mb-4">
            <strong>Active Workers:</strong> Query Celery to see currently registered workers
          </v-alert>

          <v-table density="compact">
            <thead>
              <tr>
                <th>Worker Name</th>
                <th>Queue</th>
                <th>Concurrency</th>
                <th>Tasks Processed</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><code>media@kairo</code></td>
                <td><v-chip size="small" color="primary">media</v-chip></td>
                <td>4 processes</td>
                <td>-</td>
                <td><v-chip size="small" color="success">Active</v-chip></td>
              </tr>
            </tbody>
          </v-table>

          <v-card variant="tonal" color="warning" class="pa-3 mt-4">
            <p class="text-caption mb-2"><strong>Note:</strong> Real-time worker monitoring requires backend API integration</p>
            <p class="text-caption mb-0">
              To check active workers manually, run on whisper:
            </p>
            <pre class="text-caption bg-grey-darken-4 white--text pa-2 rounded mt-2" style="overflow-x: auto;">docker exec show-build-server python -c "from celery_app import celery_app; print(list(celery_app.control.inspect().stats().keys()))"</pre>
          </v-card>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <!-- Deployment Form -->
    <v-divider class="my-6"></v-divider>

    <h4 class="text-h6 mb-4">Deploy New Worker</h4>

    <v-form ref="deploymentFormRef">
      <v-row>
        <!-- Hostname/IP -->
        <v-col cols="12" md="6">
          <v-text-field
            v-model="deployment.hostname"
            label="Remote Server Hostname/IP"
            placeholder="kairo or 192.168.51.197"
            persistent-hint
            hint="Hostname (from ~/.ssh/config) or IP address of remote Linux server"
            prepend-icon="mdi-server"
            variant="outlined"
            density="comfortable"
            :rules="[rules.required]"
          >
            <template v-slot:append-inner>
              <v-tooltip text="Must be accessible via SSH with key authentication">
                <template v-slot:activator="{ props }">
                  <v-icon v-bind="props" size="small" color="info">mdi-information</v-icon>
                </template>
              </v-tooltip>
            </template>
          </v-text-field>
        </v-col>

        <!-- Worker Name -->
        <v-col cols="12" md="6">
          <v-text-field
            v-model="deployment.workerName"
            label="Worker Name"
            placeholder="media_worker"
            persistent-hint
            hint="Unique identifier for this worker (alphanumeric, underscores allowed)"
            prepend-icon="mdi-account-hard-hat"
            variant="outlined"
            density="comfortable"
            :rules="[rules.required, rules.workerName]"
          >
            <template v-slot:append-inner>
              <v-tooltip text="Will appear as {workerName}@{hostname} in Celery">
                <template v-slot:activator="{ props }">
                  <v-icon v-bind="props" size="small" color="info">mdi-information</v-icon>
                </template>
              </v-tooltip>
            </template>
          </v-text-field>
        </v-col>
      </v-row>

      <v-row>
        <!-- Queue Name -->
        <v-col cols="12" md="6">
          <v-select
            v-model="deployment.queueName"
            label="Task Queue"
            :items="queueOptions"
            item-title="label"
            item-value="value"
            persistent-hint
            hint="Which queue should this worker consume tasks from?"
            prepend-icon="mdi-inbox-multiple"
            variant="outlined"
            density="comfortable"
            :rules="[rules.required]"
          >
            <template v-slot:item="{ props, item }">
              <v-list-item v-bind="props">
                <template v-slot:prepend>
                  <v-icon :color="item.raw.color">{{ item.raw.icon }}</v-icon>
                </template>
                <v-list-item-title>{{ item.raw.label }}</v-list-item-title>
                <v-list-item-subtitle>{{ item.raw.description }}</v-list-item-subtitle>
              </v-list-item>
            </template>
          </v-select>
        </v-col>

        <!-- Concurrency -->
        <v-col cols="12" md="6">
          <v-text-field
            v-model.number="deployment.concurrency"
            label="Concurrency (Worker Processes)"
            type="number"
            min="1"
            max="16"
            persistent-hint
            hint="Number of parallel worker processes (1-16, recommended: CPU cores)"
            prepend-icon="mdi-cpu-64-bit"
            variant="outlined"
            density="comfortable"
            :rules="[rules.required, rules.concurrency]"
          />
        </v-col>
      </v-row>

      <v-divider class="my-4"></v-divider>

      <h5 class="text-subtitle-1 mb-3">Redis Broker Configuration</h5>
      <v-row>
        <v-col cols="12" md="4">
          <v-text-field
            v-model="deployment.redisHost"
            label="Redis Host"
            placeholder="192.168.51.223"
            persistent-hint
            hint="IP address of Redis broker (farmhouse)"
            prepend-icon="mdi-server-network"
            variant="outlined"
            density="comfortable"
            :rules="[rules.required]"
          />
        </v-col>
        <v-col cols="12" md="4">
          <v-text-field
            v-model.number="deployment.redisPort"
            label="Redis Port"
            type="number"
            placeholder="6379"
            persistent-hint
            hint="Redis TCP port (default: 6379)"
            prepend-icon="mdi-lan"
            variant="outlined"
            density="comfortable"
            :rules="[rules.required, rules.port]"
          />
        </v-col>
        <v-col cols="12" md="4">
          <v-text-field
            v-model="deployment.redisPassword"
            label="Redis Password"
            type="password"
            placeholder="showbuild2025"
            persistent-hint
            hint="Password for Redis authentication"
            prepend-icon="mdi-lock"
            variant="outlined"
            density="comfortable"
            :rules="[rules.required]"
          />
        </v-col>
      </v-row>

      <v-divider class="my-4"></v-divider>

      <h5 class="text-subtitle-1 mb-3">Advanced Options</h5>
      <v-row>
        <v-col cols="12" md="6">
          <v-text-field
            v-model="deployment.volumeEpisodes"
            label="Episodes Volume Path"
            placeholder="/mnt/sync/disaffected/episodes"
            persistent-hint
            hint="Path to episodes directory on remote server"
            prepend-icon="mdi-folder-open"
            variant="outlined"
            density="comfortable"
          />
        </v-col>
        <v-col cols="12" md="6">
          <v-text-field
            v-model="deployment.volumeSharedMedia"
            label="Shared Media Volume Path"
            placeholder="/mnt/sync/shared_media"
            persistent-hint
            hint="Path to shared media directory on remote server"
            prepend-icon="mdi-folder-star"
            variant="outlined"
            density="comfortable"
          />
        </v-col>
      </v-row>

      <!-- Action Buttons -->
      <v-row class="mt-4">
        <v-col cols="12">
          <v-btn
            color="primary"
            size="large"
            prepend-icon="mdi-cloud-upload"
            @click="generateDeploymentScript"
            :disabled="!isFormValid"
          >
            Generate Deployment Script
          </v-btn>
          <v-btn
            variant="outlined"
            size="large"
            prepend-icon="mdi-refresh"
            class="ml-2"
            @click="resetForm"
          >
            Reset Form
          </v-btn>
        </v-col>
      </v-row>
    </v-form>

    <!-- Generated Script Output -->
    <v-expand-transition>
      <v-card v-if="generatedScript" variant="outlined" class="mt-6">
        <v-card-title class="bg-grey-lighten-4">
          <v-icon left class="mr-2">mdi-code-braces</v-icon>
          Generated Deployment Command
        </v-card-title>
        <v-card-text>
          <v-alert type="success" variant="tonal" class="mb-4">
            <strong>Ready to Deploy!</strong> Copy the command below and run it on the Show-Build server (whisper)
          </v-alert>

          <p class="text-subtitle-2 mb-2">Deployment Script Command:</p>
          <v-code class="pa-3 bg-grey-darken-4 white--text rounded" style="display: block; overflow-x: auto;">
            <pre>{{ generatedScript }}</pre>
          </v-code>

          <v-row class="mt-4">
            <v-col cols="12">
              <v-btn
                color="success"
                prepend-icon="mdi-content-copy"
                @click="copyToClipboard(generatedScript)"
              >
                Copy to Clipboard
              </v-btn>
              <v-btn
                variant="outlined"
                prepend-icon="mdi-download"
                class="ml-2"
                @click="downloadScript"
              >
                Download as .sh File
              </v-btn>
            </v-col>
          </v-row>

          <v-alert type="info" variant="tonal" class="mt-4">
            <p class="mb-2"><strong>Next Steps:</strong></p>
            <ol class="pl-4">
              <li>SSH into whisper: <code>ssh whisper</code></li>
              <li>Navigate to scripts directory: <code>cd /mnt/process/show-build/scripts</code></li>
              <li>Paste and run the command above</li>
              <li>Wait for deployment to complete (~2 minutes)</li>
              <li>Verify worker registration in "Current Deployments" section</li>
            </ol>
          </v-alert>
        </v-card-text>
      </v-card>
    </v-expand-transition>

    <!-- LLM Instructions Section -->
    <v-divider class="my-6"></v-divider>

    <v-expansion-panels variant="accordion">
      <v-expansion-panel>
        <v-expansion-panel-title class="text-subtitle-1 font-weight-medium">
          <v-icon left class="mr-2" color="purple">mdi-robot</v-icon>
          Instructions for LLM Integration
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <v-card variant="outlined" class="pa-4">
            <h4 class="text-subtitle-2 mb-3">Backend API Requirements</h4>

            <p class="text-body-2 mb-3">
              To enable automated deployments from this UI, implement the following backend endpoints:
            </p>

            <v-alert type="warning" variant="tonal" density="compact" class="mb-4">
              <strong>Security Note:</strong> Deployment endpoints should require admin-level authentication and validate all inputs.
            </v-alert>

            <h5 class="text-subtitle-2 mb-2">1. Worker Status Endpoint</h5>
            <v-code class="pa-3 bg-grey-lighten-4 rounded mb-4" style="display: block; overflow-x: auto;">
              <pre>GET /api/workers/status

Response:
{
  "workers": [
    {
      "name": "media@kairo",
      "hostname": "kairo",
      "queue": "media",
      "concurrency": 4,
      "tasks_processed": 142,
      "uptime": 86400,
      "status": "active"
    }
  ]
}</pre>
            </v-code>

            <h5 class="text-subtitle-2 mb-2">2. Deploy Worker Endpoint</h5>
            <v-code class="pa-3 bg-grey-lighten-4 rounded mb-4" style="display: block; overflow-x: auto;">
              <pre>POST /api/workers/deploy

Request Body:
{
  "hostname": "proxima",
  "worker_name": "media_worker",
  "queue_name": "media",
  "concurrency": 4,
  "redis_host": "192.168.51.223",
  "redis_port": 6379,
  "redis_password": "showbuild2025",
  "volume_episodes": "/mnt/sync/disaffected/episodes",
  "volume_shared_media": "/mnt/sync/shared_media"
}

Response:
{
  "task_id": "deploy-abc123",
  "status": "queued",
  "message": "Worker deployment initiated"
}</pre>
            </v-code>

            <h5 class="text-subtitle-2 mb-2">3. Deployment Status Endpoint</h5>
            <v-code class="pa-3 bg-grey-lighten-4 rounded mb-4" style="display: block; overflow-x: auto;">
              <pre>GET /api/workers/deploy/{task_id}/status

Response:
{
  "task_id": "deploy-abc123",
  "status": "SUCCESS",
  "progress": 100,
  "logs": [
    "SSH connection verified",
    "Docker installation confirmed",
    "Configuration files uploaded",
    "Worker container started",
    "Worker registered successfully"
  ],
  "worker_name": "media@proxima"
}</pre>
            </v-code>

            <v-divider class="my-4"></v-divider>

            <h4 class="text-subtitle-2 mb-3">Backend Implementation Guide</h4>

            <p class="text-body-2 mb-3">
              Create a new router file: <code>/mnt/process/show-build/app/deployment_router.py</code>
            </p>

            <v-code class="pa-3 bg-grey-lighten-4 rounded mb-4" style="display: block; overflow-x: auto;">
              <pre>from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import subprocess
from typing import List
from auth.router import get_current_user_or_key

router = APIRouter(prefix="/api/workers", tags=["Worker Deployment"])

class WorkerDeploymentRequest(BaseModel):
    hostname: str
    worker_name: str
    queue_name: str
    concurrency: int = 4
    redis_host: str = "192.168.51.223"
    redis_port: int = 6379
    redis_password: str = "showbuild2025"
    volume_episodes: str = "/mnt/sync/disaffected/episodes"
    volume_shared_media: str = "/mnt/sync/shared_media"

@router.post("/deploy")
async def deploy_worker(
    request: WorkerDeploymentRequest,
    current_user=Depends(get_current_user_or_key)
):
    # Validate admin permissions
    # Execute deployment script
    script_path = "/mnt/process/show-build/scripts/deploy_celery_worker.sh"

    cmd = [
        script_path,
        request.hostname,
        request.worker_name,
        request.queue_name,
        str(request.concurrency)
    ]

    # Set environment variables for Redis config
    env = {
        "REDIS_HOST": request.redis_host,
        "REDIS_PORT": str(request.redis_port),
        "REDIS_PASSWORD": request.redis_password
    }

    # Execute in background (use Celery for real implementation)
    result = subprocess.run(cmd, env=env, capture_output=True)

    return {
        "status": "success" if result.returncode == 0 else "failed",
        "output": result.stdout.decode(),
        "errors": result.stderr.decode()
    }

@router.get("/status")
async def get_workers_status(current_user=Depends(get_current_user_or_key)):
    from celery_app import celery_app
    inspect = celery_app.control.inspect()

    stats = inspect.stats()
    active_queues = inspect.active_queues()

    workers = []
    if stats:
        for worker_name, worker_stats in stats.items():
            workers.append({
                "name": worker_name,
                "uptime": worker_stats.get("uptime", 0),
                "status": "active"
            })

    return {"workers": workers}</pre>
            </v-code>

            <v-divider class="my-4"></v-divider>

            <h4 class="text-subtitle-2 mb-3">Frontend Integration Steps</h4>

            <ol class="pl-4 mb-0">
              <li class="mb-2">
                <strong>Add API service method:</strong>
                <v-code class="d-block pa-2 bg-grey-lighten-4 rounded mt-1" style="overflow-x: auto;">
                  <pre>// In src/services/api.js or create src/services/workers.js
export async function deployWorker(deploymentData) {
  const response = await axios.post('/api/workers/deploy', deploymentData);
  return response.data;
}

export async function getWorkersStatus() {
  const response = await axios.get('/api/workers/status');
  return response.data;
}</pre>
                </v-code>
              </li>

              <li class="mb-2">
                <strong>Update DeploymentSettings.vue:</strong>
                <ul class="pl-4 mt-1">
                  <li>Replace <code>generateDeploymentScript()</code> with API call to <code>/api/workers/deploy</code></li>
                  <li>Add real-time status fetching in "Current Deployments" section</li>
                  <li>Implement polling for deployment progress</li>
                  <li>Add success/error notifications</li>
                </ul>
              </li>

              <li class="mb-2">
                <strong>Add deployment progress tracking:</strong>
                <v-code class="d-block pa-2 bg-grey-lighten-4 rounded mt-1" style="overflow-x: auto;">
                  <pre>async function deployWorker() {
  try {
    this.deploying = true;
    const result = await api.deployWorker(this.deployment);

    // Poll for status
    const taskId = result.task_id;
    const pollInterval = setInterval(async () => {
      const status = await api.getDeploymentStatus(taskId);
      this.deploymentProgress = status.progress;
      this.deploymentLogs = status.logs;

      if (status.status === 'SUCCESS') {
        clearInterval(pollInterval);
        this.deploying = false;
        this.showSuccessNotification();
      }
    }, 2000);
  } catch (error) {
    this.showErrorNotification(error);
  }
}</pre>
                </v-code>
              </li>

              <li>
                <strong>Add worker management actions:</strong> stop, restart, remove worker
              </li>
            </ol>
          </v-card>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </v-card>
</template>

<script>
export default {
  name: 'DeploymentSettings',
  data() {
    return {
      deployment: {
        hostname: '',
        workerName: '',
        queueName: 'media',
        concurrency: 4,
        redisHost: '192.168.51.223',
        redisPort: 6379,
        redisPassword: 'showbuild2025',
        volumeEpisodes: '/mnt/sync/disaffected/episodes',
        volumeSharedMedia: '/mnt/sync/shared_media'
      },
      queueOptions: [
        {
          value: 'media',
          label: 'Media Queue',
          description: 'FFmpeg video/audio processing (high CPU/GPU)',
          icon: 'mdi-video',
          color: 'primary'
        },
        {
          value: 'compilation',
          label: 'Compilation Queue',
          description: 'Script compilation and rendering',
          icon: 'mdi-file-document',
          color: 'secondary'
        },
        {
          value: 'quotes',
          label: 'Quotes Queue',
          description: 'Quote extraction and processing',
          icon: 'mdi-format-quote-close',
          color: 'success'
        },
        {
          value: 'assets',
          label: 'Assets Queue',
          description: 'Asset optimization and metadata extraction',
          icon: 'mdi-folder-star',
          color: 'info'
        }
      ],
      generatedScript: '',
      rules: {
        required: v => !!v || 'Required field',
        workerName: v => /^[a-zA-Z0-9_]+$/.test(v) || 'Only alphanumeric and underscores allowed',
        concurrency: v => (v >= 1 && v <= 16) || 'Must be between 1 and 16',
        port: v => (v >= 1 && v <= 65535) || 'Must be a valid port number'
      }
    }
  },
  computed: {
    isFormValid() {
      return this.deployment.hostname &&
             this.deployment.workerName &&
             this.deployment.queueName &&
             this.deployment.concurrency >= 1 &&
             this.deployment.concurrency <= 16 &&
             this.deployment.redisHost &&
             this.deployment.redisPort
    }
  },
  methods: {
    generateDeploymentScript() {
      const cmd = `./deploy_celery_worker.sh ${this.deployment.hostname} ${this.deployment.workerName} ${this.deployment.queueName} ${this.deployment.concurrency}`

      const envVars = `export REDIS_HOST="${this.deployment.redisHost}"
export REDIS_PORT="${this.deployment.redisPort}"
export REDIS_PASSWORD="${this.deployment.redisPassword}"
`

      this.generatedScript = `# SSH to whisper and run:
cd /mnt/process/show-build/scripts

# Set environment variables
${envVars}
# Execute deployment
${cmd}`
    },

    copyToClipboard(text) {
      navigator.clipboard.writeText(text)
      // Add snackbar notification here
      console.log('Copied to clipboard')
    },

    downloadScript() {
      const blob = new Blob([this.generatedScript], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `deploy-${this.deployment.workerName}.sh`
      link.click()
      URL.revokeObjectURL(url)
    },

    resetForm() {
      this.deployment = {
        hostname: '',
        workerName: '',
        queueName: 'media',
        concurrency: 4,
        redisHost: '192.168.51.223',
        redisPort: 6379,
        redisPassword: 'showbuild2025',
        volumeEpisodes: '/mnt/sync/disaffected/episodes',
        volumeSharedMedia: '/mnt/sync/shared_media'
      }
      this.generatedScript = ''
    }
  }
}
</script>

<style scoped>
.v-code {
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
}

pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
