<template>
  <section class="viewer-panel" aria-label="3D 立方体画布">
    <div class="viewer-surface">
      <canvas ref="canvasRef" class="viewer-canvas" />

      <div v-if="isLoading" class="viewer-loading" aria-live="polite">
        正在加载 3D 场景...
      </div>
    </div>

    <div class="viewer-status">
      <span :class="['status-dot', apiStatus === 'online' ? 'is-online' : '']" />
      <span>FastAPI: {{ apiStatus }}</span>
      <span>{{ cubes.length }} cubes</span>
    </div>
  </section>
</template>

<script setup>
import { onMounted, onUnmounted, watch, ref } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js'
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js'
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js'
import { SSAOPass } from 'three/addons/postprocessing/SSAOPass.js'
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js'
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js'

const props = defineProps({
  cubes: {
    type: Array,
    default: () => [],
  },
  apiStatus: {
    type: String,
    default: 'checking',
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
})

const PLANE_SIZE = 12
const CUBE_BASE_SIZE = 0.9

const canvasRef = ref(null)

let renderer
let scene
let camera
let controls
let plane
let cubeGroup
let composer
let ssaoPass
let environmentTexture
let contactShadowTexture
let animationFrameId
let clock

onMounted(() => {
  createScene()
  redrawCubes()
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

watch(
  () => props.cubes,
  () => {
    redrawCubes()
  },
  { deep: true },
)

function createScene() {
  scene = new THREE.Scene()
  scene.fog = new THREE.FogExp2('#d5e5f3', 0.0065)
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
  renderer.toneMappingExposure = 0.82
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
    color: '#dce5ee',
    roughness: 0.5,
    metalness: 0.02,
    clearcoat: 0.28,
    clearcoatRoughness: 0.62,
    envMapIntensity: 0.32,
  })
  plane = new THREE.Mesh(geometry, material)
  plane.rotation.x = -Math.PI / 2
  plane.receiveShadow = true

  const grid = new THREE.GridHelper(PLANE_SIZE, PLANE_SIZE, '#8ea6bb', '#ccd9e4')
  grid.position.y = 0.01
  grid.material.opacity = 0.42
  grid.material.transparent = true
  grid.material.depthWrite = false

  const planeGroup = new THREE.Group()
  planeGroup.add(plane, grid)
  return planeGroup
}

function createLights() {
  const lightGroup = new THREE.Group()
  const ambientLight = new THREE.HemisphereLight('#f7fbff', '#b8c9d8', 0.96)
  const directionalLight = new THREE.DirectionalLight('#fff9f0', 1.92)
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

  const rimLight = new THREE.DirectionalLight('#d7ebff', 0.58)
  rimLight.position.set(-5, 4, -6)

  const softFill = new THREE.RectAreaLight('#ffffff', 0.6, 6, 5)
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

  const bloomPass = new UnrealBloomPass(new THREE.Vector2(1, 1), 0.006, 0.4, 0.96)
  composer.addPass(bloomPass)
  composer.addPass(new OutputPass())
}

function redrawCubes() {
  if (!cubeGroup) return

  disposeObject(cubeGroup)
  cubeGroup.clear()

  props.cubes.forEach((cube) => {
    addCubeAt(cube.x, cube.z, cube.height, cube)
  })
}

function addCubeAt(relativeX, relativeZ, height, options = {}) {
  const safeX = clampRelative(relativeX)
  const safeZ = clampRelative(relativeZ)
  const safeHeight = Math.max(0.2, Number(height) || 1)
  const cubeColor = new THREE.Color(options.color || '#f7f9fc')
  const faceColor = cubeColor.clone().lerp(new THREE.Color('#ffffff'), 0.18)
  const edgeGlow = cubeColor.clone().lerp(new THREE.Color('#ffffff'), 0.62)
  const geometry = new RoundedBoxGeometry(CUBE_BASE_SIZE, safeHeight, CUBE_BASE_SIZE, 8, 0.08)
  const material = new THREE.MeshPhysicalMaterial({
    color: faceColor,
    emissive: edgeGlow,
    emissiveIntensity: 0.04,
    metalness: 0.02,
    roughness: 0.34,
    clearcoat: 0.48,
    clearcoatRoughness: 0.42,
    envMapIntensity: 0.58,
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
      opacity: 0.28,
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
  if (!canvas || !camera || !renderer || !composer) return

  const width = canvas.clientWidth
  const height = canvas.clientHeight

  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height, false)
  composer.setSize(width, height)

  if (ssaoPass) {
    ssaoPass.setSize(width, height)
  }
}

function animate() {
  animationFrameId = requestAnimationFrame(animate)

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
