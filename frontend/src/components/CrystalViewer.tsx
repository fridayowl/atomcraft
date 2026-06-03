import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'

const ELEMENT_COLORS: Record<string, string> = {
  H: '#ffffff', Li: '#b1c8e8', Be: '#5cf25c', B: '#ffb5b5', C: '#909090',
  N: '#3050f8', O: '#ff0d0d', F: '#90e050', Na: '#ab5cf2', Mg: '#8aff00',
  Al: '#bfa6a6', Si: '#f0c8a0', P: '#ff8000', S: '#ffff30', Cl: '#1ff01f',
  K: '#8f40d4', Ca: '#3dff00', Ti: '#bfc2c7', V: '#a6a6ab', Cr: '#8a99c7',
  Mn: '#9c7ac7', Fe: '#e06633', Co: '#f090a0', Ni: '#50d050', Cu: '#c88033',
  Zn: '#7d80b0', Zr: '#94d1e0', Nb: '#73c2c2', Mo: '#54b5b5', Sn: '#668080',
  Sb: '#9e6363', Te: '#d47a00', Ba: '#00c900', Ta: '#4da6a6', W: '#2194d6',
  Pt: '#a0a0d0', Au: '#d0d000', Pb: '#575961', Bi: '#9e4f5c',
}

const DEFAULT_COLOR = '#888888'

function getElementColor(element: string): string {
  return ELEMENT_COLORS[element] || DEFAULT_COLOR
}

function getElementRadius(element: string): number {
  const radii: Record<string, number> = {
    H: 0.25, Li: 0.45, Be: 0.35, B: 0.30, C: 0.30, N: 0.30, O: 0.30, F: 0.28,
    Na: 0.55, Mg: 0.45, Al: 0.40, Si: 0.40, P: 0.38, S: 0.38, Cl: 0.35,
    K: 0.65, Ca: 0.55, Ti: 0.50, V: 0.48, Cr: 0.48, Mn: 0.46, Fe: 0.46,
    Co: 0.44, Ni: 0.44, Cu: 0.44, Zn: 0.44, Zr: 0.55, Nb: 0.52, Mo: 0.52,
    Sn: 0.50, Sb: 0.48, Te: 0.48, Ba: 0.65, Ta: 0.55, W: 0.52, Pt: 0.48,
    Au: 0.48, Pb: 0.52, Bi: 0.52,
  }
  return radii[element] || 0.35
}

function Atom({ position, element }: { position: [number, number, number]; element: string }) {
  const radius = getElementRadius(element)
  return (
    <mesh position={position}>
      <sphereGeometry args={[radius, 24, 24]} />
      <meshStandardMaterial color={getElementColor(element)} roughness={0.3} metalness={0.1} />
    </mesh>
  )
}

function Bond({ start, end }: { start: [number, number, number]; end: [number, number, number] }) {
  const s = useMemo(() => new THREE.Vector3(...start), [start])
  const e = useMemo(() => new THREE.Vector3(...end), [end])
  const dir = useMemo(() => e.clone().sub(s), [s, e])
  const length = dir.length()
  const mid = useMemo(() => [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2, (start[2] + end[2]) / 2] as [number, number, number], [start, end])
  const quat = useMemo(() => new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize()), [dir])

  return (
    <mesh position={mid} quaternion={quat}>
      <cylinderGeometry args={[0.04, 0.04, length, 6]} />
      <meshStandardMaterial color="#888888" transparent opacity={0.4} />
    </mesh>
  )
}

function CrystalStructure({ atoms, bonds }: {
  atoms: { element: string; x: number; y: number; z: number }[]
  bonds: [[number, number, number], [number, number, number]][]
}) {
  const groupRef = useRef<THREE.Group>(null)

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.15
    }
  })

  return (
    <group ref={groupRef}>
      {atoms.map((atom, i) => (
        <Atom key={i} position={[atom.x, atom.y, atom.z]} element={atom.element} />
      ))}
      {bonds.map((bond, i) => (
        <Bond key={i} start={bond[0]} end={bond[1]} />
      ))}
    </group>
  )
}

interface CrystalViewerProps {
  structure?: {
    atoms: { element: string; x: number; y: number; z: number }[]
    lattice: { a: number; b: number; c: number }
  } | null
  elements?: string[]
  latticeParameters?: { a: number | null; b: number | null; c: number | null }
}

export default function CrystalViewer({ structure, elements, latticeParameters }: CrystalViewerProps) {
  const { atoms, bonds } = useMemo(() => {
    if (structure && structure.atoms && structure.atoms.length > 0) {
      const positions = structure.atoms.map(a => [a.x, a.y, a.z] as [number, number, number])
      const bnds: [[number, number, number], [number, number, number]][] = []
      for (let i = 0; i < positions.length; i++) {
        for (let j = i + 1; j < positions.length; j++) {
          const dx = positions[i][0] - positions[j][0]
          const dy = positions[i][1] - positions[j][1]
          const dz = positions[i][2] - positions[j][2]
          const dist = Math.sqrt(dx * dx + dy * dy + dz * dz)
          const maxDist = Math.max(structure.lattice.a, structure.lattice.b, structure.lattice.c) * 0.6
          if (dist < maxDist && dist > 0.05) {
            bnds.push([positions[i], positions[j]])
          }
        }
      }
      return { atoms: structure.atoms, bonds: bnds }
    }

    const a = latticeParameters?.a || 5
    const b = latticeParameters?.b || 5
    const c = latticeParameters?.c || 5
    const elems = (elements?.length ? elements : ['Fe', 'O']).slice(0, 8)

    const basePositions: [number, number, number][] = [
      [0, 0, 0], [a/2, b/2, 0], [0, b/2, c/2], [a/2, 0, c/2],
      [a/4, b/4, c/4], [3*a/4, 3*b/4, c/4], [3*a/4, b/4, 3*c/4], [a/4, 3*b/4, 3*c/4],
    ]

    const atoms = basePositions.slice(0, elems.length).map((pos, i) => ({
      element: elems[i],
      x: pos[0], y: pos[1], z: pos[2],
    }))

    const bnds: [[number, number, number], [number, number, number]][] = []
    for (let i = 0; i < atoms.length; i++) {
      for (let j = i + 1; j < atoms.length; j++) {
        const p = [atoms[i].x, atoms[i].y, atoms[i].z] as [number, number, number]
        const q = [atoms[j].x, atoms[j].y, atoms[j].z] as [number, number, number]
        const dx = p[0] - q[0]; const dy = p[1] - q[1]; const dz = p[2] - q[2]
        const dist = Math.sqrt(dx*dx + dy*dy + dz*dz)
        if (dist < Math.max(a, b, c) * 0.75 && dist > 0.1) {
          bnds.push([p, q])
        }
      }
    }

    return { atoms, bonds: bnds }
  }, [structure, elements, latticeParameters])

  const center = useMemo(() => {
    if (atoms.length === 0) return [0, 0, 0]
    const cx = atoms.reduce((s, a) => s + a.x, 0) / atoms.length
    const cy = atoms.reduce((s, a) => s + a.y, 0) / atoms.length
    const cz = atoms.reduce((s, a) => s + a.z, 0) / atoms.length
    return [cx, cy, cz] as [number, number, number]
  }, [atoms])

  return (
    <div className="w-full h-64 glass rounded-xl overflow-hidden">
      <Canvas camera={{ position: [6, 4, 8], fov: 40 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 10]} intensity={0.8} />
        <directionalLight position={[-5, -5, -5]} intensity={0.3} />
        <group position={[-center[0], -center[1], -center[2]]}>
          <CrystalStructure atoms={atoms} bonds={bonds} />
        </group>
        <OrbitControls enablePan={true} minDistance={2} maxDistance={20} />
      </Canvas>
    </div>
  )
}
