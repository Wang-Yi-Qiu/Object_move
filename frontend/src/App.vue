<template>
  <main class="app-shell">
    <div class="atmosphere" aria-hidden="true">
      <span class="sky-haze sky-haze-a" />
      <span class="sky-haze sky-haze-b" />
      <span class="sky-haze sky-haze-c" />
    </div>

    <nav class="top-nav" aria-label="主导航">
      <a class="brand" href="#" aria-label="回到控制台">
        <span class="brand-mark">3D</span>
        <span>Spatial Console</span>
      </a>

      <div class="nav-links" aria-label="页面导航">
        <a href="#studio">Studio</a>
        <a href="#controls">Controls</a>
        <a href="#metrics">Metrics</a>
      </div>

      <div class="nav-actions">
        <button class="icon-button" type="button" aria-label="聚焦控制面板" @click="scrollToControls">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 8.3a3.7 3.7 0 1 0 0 7.4 3.7 3.7 0 0 0 0-7.4Z" />
            <path
              d="M19.4 13.2c.1-.4.1-.8.1-1.2s0-.8-.1-1.2l2-1.5-2-3.4-2.3.9c-.6-.5-1.3-.9-2.1-1.2L14.7 3H10l-.4 2.6c-.8.3-1.5.7-2.1 1.2l-2.3-.9-2 3.4 2 1.5c-.1.4-.1.8-.1 1.2s0 .8.1 1.2l-2 1.5 2 3.4 2.3-.9c.6.5 1.3.9 2.1 1.2l.4 2.6h4.7l.4-2.6c.8-.3 1.5-.7 2.1-1.2l2.3.9 2-3.4-2.1-1.5Z"
            />
          </svg>
        </button>
        <span class="avatar" aria-label="用户头像">W</span>
      </div>
    </nav>

    <section class="hero" id="studio">
      <div class="hero-copy">
        <p class="system-line">Vue 3 + Three.js + FastAPI</p>
        <h1>平面立方体绘制</h1>
        <p class="intro">
          在大平面上输入相对坐标和高度，前端会请求接口并在 3D 场景里生成对应立方体。
        </p>
        <div class="hero-actions">
          <button class="primary-action" type="button" @click="scrollToControls">开始创建</button>
          <a class="secondary-action" href="#metrics">查看状态</a>
        </div>
      </div>

      <div class="metric-strip" id="metrics" aria-label="场景指标">
        <div class="metric-card">
          <span>Cubes</span>
          <strong>{{ cubeRecords.length }}</strong>
        </div>
        <div class="metric-card">
          <span>Max height</span>
          <strong>{{ maxHeight.toFixed(1) }}</strong>
        </div>
        <div class="metric-card">
          <span>API</span>
          <strong>{{ health.api }}</strong>
        </div>
      </div>
    </section>

    <section class="workspace">
      <SceneCanvas :cubes="cubeRecords" :api-status="health.api" :is-loading="isLoadingCubes" />

      <aside class="side-panel" id="controls">
        <div class="panel-heading">
          <p class="eyebrow">Build Surface</p>
          <h2>创建几何体</h2>
        </div>

        <div class="panel-summary">
          <span>Scene</span>
          <strong>{{ health.api === 'online' ? 'Connected' : 'Fallback mode' }}</strong>
          <small>{{ isLoadingCubes ? '正在同步立方体数据' : '准备创建新的立方体' }}</small>
        </div>

        <form class="cube-form" @submit.prevent="submitCube">
          <label>
            <span>X 相对坐标</span>
            <input v-model.number="draftCube.x" type="number" min="-1" max="1" step="0.1" />
          </label>
          <label>
            <span>Z 相对坐标</span>
            <input v-model.number="draftCube.z" type="number" min="-1" max="1" step="0.1" />
          </label>
          <label>
            <span>高度</span>
            <input v-model.number="draftCube.height" type="number" min="0.2" max="8" step="0.2" />
          </label>
          <label>
            <span>颜色</span>
            <input v-model="draftCube.color" type="color" />
          </label>
          <button type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? '生成中...' : '生成立方体' }}
          </button>
        </form>

        <div v-if="errorMessage" class="notice">
          {{ errorMessage }}
        </div>

        <div class="cube-list" aria-label="已生成立方体">
          <div v-for="cube in cubeRecords" :key="cube.id" class="cube-item">
            <span class="cube-color" :style="{ backgroundColor: cube.color }" />
            <span>
              <strong>{{ cube.name }}</strong>
              <small>x {{ cube.x.toFixed(2) }} · z {{ cube.z.toFixed(2) }} · h {{ cube.height.toFixed(1) }}</small>
            </span>
          </div>
        </div>
      </aside>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import SceneCanvas from './components/SceneCanvas.vue'

const cubeRecords = ref([])
const errorMessage = ref('')
const isLoadingCubes = ref(true)
const isSubmitting = ref(false)
const health = ref({ api: 'checking' })
const draftCube = reactive({
  x: 0,
  z: 0,
  height: 1.4,
  color: '#f7f9fc',
})

const maxHeight = computed(() =>
  cubeRecords.value.reduce((max, cube) => Math.max(max, Number(cube.height) || 0), 0),
)

const fallbackCubes = [
  { id: 'local-1', name: '中心立方体', x: 0, z: 0, height: 2.2, color: '#f7f9fc' },
  { id: 'local-2', name: '左前立方体', x: -0.55, z: 0.38, height: 1.2, color: '#edf3fb' },
  { id: 'local-3', name: '右后立方体', x: 0.48, z: -0.42, height: 3.4, color: '#ffffff' },
]

onMounted(async () => {
  await Promise.all([loadHealth(), loadCubes()])
})

async function loadHealth() {
  try {
    const { response, data } = await requestJson('/api/health')
    health.value.api = data.ok ? 'online' : 'offline'
  } catch {
    health.value.api = 'offline'
  }
}

async function loadCubes() {
  isLoadingCubes.value = true

  try {
    const { response, data } = await requestJson('/api/cubes')

    if (!response.ok) {
      throw new Error(data.detail || '立方体接口请求失败')
    }

    cubeRecords.value = data
    errorMessage.value = ''
  } catch (error) {
    errorMessage.value = `${error.message}，现在使用前端备用立方体。`
    cubeRecords.value = fallbackCubes
  } finally {
    isLoadingCubes.value = false
  }
}

async function submitCube() {
  isSubmitting.value = true

  const cube = {
    name: `立方体 ${cubeRecords.value.length + 1}`,
    x: draftCube.x,
    z: draftCube.z,
    height: draftCube.height,
    color: draftCube.color,
  }

  try {
    const { response, data } = await requestJson('/api/cubes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cube),
    })

    if (!response.ok) {
      throw new Error(data.detail || '立方体创建失败')
    }

    cubeRecords.value = [...cubeRecords.value, data]
    resetDraft()
    errorMessage.value = ''
  } catch (error) {
    const localCube = {
      ...cube,
      id: `local-${Date.now()}`,
      x: clampRelative(cube.x),
      z: clampRelative(cube.z),
      height: Math.max(0.2, Number(cube.height) || 1),
    }

    cubeRecords.value = [...cubeRecords.value, localCube]
    resetDraft()
    errorMessage.value = `${error.message}，已先在本地画布生成。`
  } finally {
    isSubmitting.value = false
  }
}

function resetDraft() {
  draftCube.x = 0
  draftCube.z = 0
  draftCube.height = 1.4
  draftCube.color = '#f7f9fc'
}

function clampRelative(value) {
  const numberValue = Number(value)

  if (Number.isNaN(numberValue)) return 0
  return Math.min(1, Math.max(-1, numberValue))
}

function scrollToControls() {
  document.getElementById('controls')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function requestJson(url, options) {
  const response = await fetch(url, options)
  const raw = await response.text()

  if (!raw) {
    return { response, data: {} }
  }

  try {
    return { response, data: JSON.parse(raw) }
  } catch {
    throw new Error('后端暂时没有返回可用数据')
  }
}
</script>
