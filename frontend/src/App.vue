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
        <button class="icon-button" type="button" aria-label="设置">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 8.3a3.7 3.7 0 1 0 0 7.4 3.7 3.7 0 0 0 0-7.4Z" />
            <path d="M19.4 13.2c.1-.4.1-.8.1-1.2s0-.8-.1-1.2l2-1.5-2-3.4-2.3.9c-.6-.5-1.3-.9-2.1-1.2L14.7 3H10l-.4 2.6c-.8.3-1.5.7-2.1 1.2l-2.3-.9-2 3.4 2 1.5c-.1.4-.1.8-.1 1.2s0 .8.1 1.2l-2 1.5 2 3.4 2.3-.9c.6.5 1.3.9 2.1 1.2l.4 2.6h4.7l.4-2.6c.8-.3 1.5-.7 2.1-1.2l2.3.9 2-3.4-2.1-1.5Z" />
          </svg>
        </button>
        <span class="avatar" aria-label="用户头像">W</span>
      </div>
    </nav>

    <section class="hero" id="studio">
      <div class="hero-copy">
        <p class="system-line">Vue + Three.js + FastAPI</p>
        <h1>平面立方体绘制</h1>
        <p class="intro">
          在大平面上输入相对坐标和高度，调用绘制函数后会在对应位置生成立方体。
        </p>
        <div class="hero-actions">
          <button class="primary-action" type="button" @click="submitCube">生成立方体</button>
          <a class="secondary-action" href="#controls">调整参数</a>
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
      <section class="viewer-panel" aria-label="3D 立方体画布">
        <canvas ref="canvasRef" class="viewer-canvas" />
        <div class="viewer-status">
          <span :class="['status-dot', health.api === 'online' ? 'is-online' : '']" />
          <span>FastAPI: {{ health.api }}</span>
          <span>{{ cubeRecords.length }} cubes</span>
        </div>
      </section>

      <aside class="side-panel" id="controls">
        <div class="panel-heading">
          <p class="eyebrow">Build Surface</p>
          <h2>创建几何体</h2>
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
          <button type="button" @click="submitCube">生成立方体</button>
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
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js'
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js'
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js'
import { SSAOPass } from 'three/addons/postprocessing/SSAOPass.js'
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js'
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js'

const PLANE_SIZE = 12
const CUBE_BASE_SIZE = 0.9

const canvasRef = ref(null)
const cubeRecords = ref([])
const errorMessage = ref('')
const health = ref({ api: 'checking' })
const draftCube = reactive({
  x: 0,
  z: 0,
  height: 1.5,
  color: '#f7f9fc',
})

const maxHeight = computed(() =>
  cubeRecords.value.reduce((max, cube) => Math.max(max, Number(cube.height) || 0), 0),
)

let renderer
let scene
let camera
let controls
let plane
let cubeGroup
let composer
let bloomPass
let ssaoPass
let environmentTexture
let contactShadowTexture
let animationFrameId
let clock

const fallbackCubes = [
  { id: 'local-1', name: '中心立方体', x: 0, z: 0, height: 2.2, color: '#f7f9fc' },
  { id: 'local-2', name: '左前立方体', x: -0.55, z: 0.38, height: 1.2, color: '#edf3fb' },
  { id: 'local-3', name: '右后立方体', x: 0.48, z: -0.42, height: 3.4, color: '#ffffff' },
]

onMounted(async () => {
  createScene()
  await loadHealth()
  await loadCubes()
  window.addEventListener('resize', resizeRenderer)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeRenderer)
  cancelAnimationFrame(animationFrameId)
  controls?.dispose()
  disposeObject(cubeGroup)
  plane?.geometry?.dispose()
  plane?.material?.dispose()
  composer?.dispose()
  environmentTexture?.dispose()
  contactShadowTexture?.dispose()
  renderer?.dispose()
})

async function loadHealth() {
  try {
    const response = await fetch('/api/health')
    const data = await response.json()
    health.value.api = data.ok ? 'online' : 'offline'
  } catch {
    health.value.api = 'offline'
  }
}

async function loadCubes() {
  try {
    const response = await fetch('/api/cubes')
    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || '立方体接口请求失败')
    }

    cubeRecords.value = data
  } catch (error) {
    errorMessage.value = `${error.message}，现在使用前端备用立方体。`
    cubeRecords.value = fallbackCubes
  }

  redrawCubes()
}

async function submitCube() {
  const cube = {
    name: `立方体 ${cubeRecords.value.length + 1}`,
    x: draftCube.x,
    z: draftCube.z,
    height: draftCube.height,
    color: draftCube.color,
  }

  try {
    const response = await fetch('/api/cubes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cube),
    })
    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || '立方体创建失败')
    }

    cubeRecords.value = [...cubeRecords.value, data]
    addCubeAt(data.x, data.z, data.height, { id: data.id, name: data.name, color: data.color })
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
    addCubeAt(localCube.x, localCube.z, localCube.height, localCube)
    errorMessage.value = `${error.message}，已先在本地画布生成。`
  }
}

function createScene() {
  scene = new THREE.Scene()
  scene.fog = new THREE.FogExp2('#dbeeff', 0.01)
  clock = new THREE.Clock()

  camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100)
  camera.position.set(7.2, 5.8, 8.4)

  renderer = new THREE.WebGLRenderer({
    canvas: canvasRef.value,
    alpha: true,
    antialias: true,
  })
  renderer.setClearAlpha(0)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 0.94
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap

  const pmremGenerator = new THREE.PMREMGenerator(renderer)
  environmentTexture = pmremGenerator.fromScene(new RoomEnvironment(renderer), 0.04).texture
  scene.environment = environmentTexture
  pmremGenerator.dispose()

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.06
  controls.enablePan = false
  controls.minDistance = 6
  controls.maxDistance = 16
  controls.maxPolarAngle = Math.PI * 0.48
  controls.target.set(0, 0.55, 0)

  cubeGroup = new THREE.Group()
  contactShadowTexture = createContactShadowTexture()
  scene.add(cubeGroup)
  scene.add(createPlane())
  scene.add(createLights())
  createComposer()

  resizeRenderer()
  animate()
}

function createPlane() {
  const geometry = new THREE.PlaneGeometry(PLANE_SIZE, PLANE_SIZE)
  const material = new THREE.MeshPhysicalMaterial({
    color: '#e8edf2',
    roughness: 0.54,
    metalness: 0.02,
    clearcoat: 0.28,
    clearcoatRoughness: 0.7,
    envMapIntensity: 0.38,
  })
  plane = new THREE.Mesh(geometry, material)
  plane.rotation.x = -Math.PI / 2
  plane.receiveShadow = true

  const grid = new THREE.GridHelper(PLANE_SIZE, PLANE_SIZE, '#9fb5ca', '#d4e1ed')
  grid.position.y = 0.01
  grid.material.opacity = 0.25
  grid.material.transparent = true
  grid.material.depthWrite = false

  const planeGroup = new THREE.Group()
  planeGroup.add(plane, grid)
  return planeGroup
}

function createLights() {
  const lightGroup = new THREE.Group()
  const ambientLight = new THREE.HemisphereLight('#f8fcff', '#bccbda', 1.16)
  const directionalLight = new THREE.DirectionalLight('#fffaf0', 2.18)
  directionalLight.position.set(5, 9, 4)
  directionalLight.castShadow = true
  directionalLight.shadow.mapSize.set(2048, 2048)
  directionalLight.shadow.bias = -0.00018
  directionalLight.shadow.normalBias = 0.018
  directionalLight.shadow.camera.near = 0.5
  directionalLight.shadow.camera.far = 28
  directionalLight.shadow.camera.left = -9
  directionalLight.shadow.camera.right = 9
  directionalLight.shadow.camera.top = 9
  directionalLight.shadow.camera.bottom = -9

  const rimLight = new THREE.DirectionalLight('#d8f0ff', 0.82)
  rimLight.position.set(-5, 4, -6)

  const softFill = new THREE.RectAreaLight('#ffffff', 1.1, 6, 5)
  softFill.position.set(0, 5, -5)
  softFill.lookAt(0, 0, 0)

  lightGroup.add(ambientLight, directionalLight, rimLight, softFill)
  return lightGroup
}

function createComposer() {
  composer = new EffectComposer(renderer)
  composer.addPass(new RenderPass(scene, camera))

  ssaoPass = new SSAOPass(scene, camera, 1, 1)
  ssaoPass.kernelRadius = 10
  ssaoPass.minDistance = 0.008
  ssaoPass.maxDistance = 0.12
  ssaoPass.output = SSAOPass.OUTPUT.Default
  composer.addPass(ssaoPass)

  bloomPass = new UnrealBloomPass(new THREE.Vector2(1, 1), 0.018, 0.45, 0.92)
  composer.addPass(bloomPass)
  composer.addPass(new OutputPass())
}

function redrawCubes() {
  cubeGroup.clear()
  cubeRecords.value.forEach((cube) => {
    addCubeAt(cube.x, cube.z, cube.height, cube)
  })
}

function addCubeAt(relativeX, relativeZ, height, options = {}) {
  const safeX = clampRelative(relativeX)
  const safeZ = clampRelative(relativeZ)
  const safeHeight = Math.max(0.2, Number(height) || 1)
  const geometry = new RoundedBoxGeometry(CUBE_BASE_SIZE, safeHeight, CUBE_BASE_SIZE, 8, 0.08)
  const material = new THREE.MeshPhysicalMaterial({
    color: '#f2f6fa',
    emissive: options.color || '#ffffff',
    emissiveIntensity: 0.006,
    metalness: 0.02,
    roughness: 0.38,
    clearcoat: 0.42,
    clearcoatRoughness: 0.58,
    envMapIntensity: 0.62,
  })
  const cube = new THREE.Mesh(geometry, material)

  cube.name = options.name || options.id || 'cube'
  cube.castShadow = true
  cube.receiveShadow = true
  cube.position.y = safeHeight / 2
  cube.scale.y = 0.02
  cube.userData.targetScaleY = 1
  cube.userData.growthSpeed = 0.048

  const shadow = new THREE.Mesh(
    new THREE.PlaneGeometry(CUBE_BASE_SIZE * 2.1, CUBE_BASE_SIZE * 2.1),
    new THREE.MeshBasicMaterial({
      map: contactShadowTexture,
      transparent: true,
      opacity: 0.44,
      depthWrite: false,
    }),
  )
  shadow.rotation.x = -Math.PI / 2
  shadow.position.y = 0.018

  const group = new THREE.Group()
  group.name = `${cube.name}-group`
  group.position.set(
    safeX * (PLANE_SIZE / 2 - CUBE_BASE_SIZE / 2),
    0,
    safeZ * (PLANE_SIZE / 2 - CUBE_BASE_SIZE / 2),
  )
  group.add(shadow, cube)
  cubeGroup.add(group)
  return group
}

function clampRelative(value) {
  const numberValue = Number(value)

  if (Number.isNaN(numberValue)) return 0
  return Math.min(1, Math.max(-1, numberValue))
}

function resizeRenderer() {
  const canvas = canvasRef.value
  const width = canvas.clientWidth
  const height = canvas.clientHeight

  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height, false)
  composer?.setSize(width, height)
  if (ssaoPass) {
    ssaoPass.setSize(width, height)
  }
}

function animate() {
  animationFrameId = requestAnimationFrame(animate)
  const elapsed = clock.getElapsedTime()
  const drift = Math.sin(elapsed * 0.28) * 0.12

  camera.position.x += (7.2 + drift - camera.position.x) * 0.006
  camera.position.y += (5.8 + Math.sin(elapsed * 0.22) * 0.08 - camera.position.y) * 0.006

  cubeGroup.traverse((child) => {
    if (!child.isMesh || child.userData.targetScaleY === undefined) return
    child.scale.y += (child.userData.targetScaleY - child.scale.y) * child.userData.growthSpeed
  })

  controls.update()
  composer.render()
}

function disposeObject(object) {
  object?.traverse?.((child) => {
    child.geometry?.dispose?.()
    child.material?.dispose?.()
  })
}

function createContactShadowTexture() {
  const size = 128
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const context = canvas.getContext('2d')
  const gradient = context.createRadialGradient(size / 2, size / 2, 4, size / 2, size / 2, size / 2)
  gradient.addColorStop(0, 'rgba(40, 55, 75, 0.34)')
  gradient.addColorStop(0.45, 'rgba(40, 55, 75, 0.13)')
  gradient.addColorStop(1, 'rgba(40, 55, 75, 0)')
  context.fillStyle = gradient
  context.fillRect(0, 0, size, size)

  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  return texture
}
</script>
