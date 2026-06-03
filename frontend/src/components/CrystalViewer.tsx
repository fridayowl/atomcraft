import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'

const ELEMENT_COLORS: Record<string, string> = {
  Li: '#b1c8e8', Be: '#5cf25c', B: '#ffb5b5', C: '#404040', N: '#3050f8',
  O: '#ff0d0d', F: '#90e050', Na: '#ab5cf2', Mg: '#8aff00', Al: '#bfa6a6',
  Si: '#f0c8a0', P: '#ff8000', S: '#ffff30', Cl: '#1ff01f', K: '#8f40d4',
  Ca: '#3dff00', Ti: '#bfc2c7', V: '#a6a6ab', Cr: '#8a99c7', Mn: '#9c7ac7',
  Fe: '#e06633', Co: '#f090a0', Ni: '#50d050', Cu: '#c88033', Zn: '#7d80b0',
}

const DEFAULT_COLOR = '#888888'

function getElementColor(element: string): string {
  return ELEMENT_COLORS[element] || DEFAULT_COLOR
}

function Atom({ position, element, radius }: { position: [number, number, number]; element: string; radius: number }) {
  return (
    <mesh position={position}>
      <sphereGeometry args={[radius, 32, 32]} />
      <meshStandardMaterial color={getElementColor(element)} roughness={0.3} metalness={0.1} />
    </mesh>
  )
}

function Bond({ start, end }: { start: [number, number, number]; end: [number, number, number] }) {
  const direction = useMemo(() => {
    const s = new THREE.Vector3(...start)
    const e = new THREE.Vector3(...end)
    return e.clone().sub(s)
  }, [start, end])

  const length = direction.length()
  const mid = useMemo(() => {
    return [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2, (start[2] + end[2]) / 2] as [number, number, number]
  }, [start, end])

  return (
    <mesh position={mid} quaternion={useMemo(() => {
      const up = new THREE.Vector3(0, 1, 0)
      const dir = direction.clone().normalize()
      const q = new THREE.Quaternion().setFromUnitVectors(up, dir)
      return q
    }, [direction])}>
      <cylinderGeometry args={[0.06, 0.06, length, 8]} />
      <meshStandardMaterial color="#666666" transparent opacity={0.5} />
    </mesh>
  )
}

function CrystalStructure({ positions, elements, bonds }: {
  positions: [number, number, number][]
  elements: string[]
  bonds: [[number, number, number], [number, number, number]][]
}) {
  const groupRef = useRef<THREE.Group>(null)

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.2
    }
  })

  return (
    <group ref={groupRef}>
      {positions.map((pos, i) => (
        <Atom key={i} position={pos} element={elements[i]} radius={0.3} />
      ))}
      {bonds.map((bond, i) => (
        <Bond key={i} start={bond[0]} end={bond[1]} />
      ))}
    </group>
  )
}

interface CrystalViewerProps {
  elements: string[]
  latticeParameters: {
    a: number | null
    b: number | null
    c: number | null
  }
}

export default function CrystalViewer({ elements, latticeParameters }: CrystalViewerProps) {
  const { positions, elements: elems, bonds } = useMemo(() => {
    const a = latticeParameters.a || 5
    const b = latticeParameters.b || 5
    const c = latticeParameters.c || 5

    const elems = elements.length > 0 ? elements : ['Fe', 'O']
    const basePositions: [number, number, number][] = [
      [0, 0, 0], [a / 2, b / 2, 0], [0, b / 2, c / 2], [a / 2, 0, c / 2],
      [a / 4, b / 4, c / 4], [3 * a / 4, 3 * b / 4, c / 4], [3 * a / 4, b / 4, 3 * c / 4], [a / 4, 3 * b / 4, 3 * c / 4],
    ]
    const positions = basePositions.slice(0, Math.max(elems.length, 4))

    const mapped: [number, number, number][] = []
    const mappedElems: string[] = []
    for (let i = 0; i < positions.length; i++) {
      mapped.push(positions[i % positions.length])
      mappedElems.push(elems[i % elems.length])
    }

    const bonds: [[number, number, number], [number, number, number]][] = []
    for (let i = 0; i < mapped.length; i++) {
      for (let j = i + 1; j < mapped.length; j++) {
        const dx = mapped[i][0] - mapped[j][0]
        const dy = mapped[i][1] - mapped[j][1]
        const dz = mapped[i][2] - mapped[j][2]
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz)
        if (dist < Math.max(a, b, c) * 0.75 && dist > 0.1) {
          bonds.push([mapped[i], mapped[j]])
        }
      }
    }

    return { positions: mapped, elements: mappedElems, bonds }
  }, [elements, latticeParameters])

  return (
    <div className="w-full h-64 glass rounded-xl overflow-hidden">
      <Canvas camera={{ position: [6, 4, 8], fov: 40 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 10]} intensity={0.8} />
        <directionalLight position={[-5, -5, -5]} intensity={0.3} />
        <CrystalStructure positions={positions} elements={elems} bonds={bonds} />
        <OrbitControls enablePan={false} minDistance={3} maxDistance={20} />
      </Canvas>
    </div>
  )
}
