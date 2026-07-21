import { create } from 'zustand'

// --- Tipos existentes ---
interface Chip {
  id: string
  label: string
  active: boolean
  type?: string
}

// --- Timeline ---
interface TimelineItem {
  id: string
  label: string
  status: 'pending' | 'running' | 'done'
}

// --- Resolução de ingredientes (contrato IngredientResolution) ---
interface PendingResolution {
  original_input: string
  normalized_input?: string
  resolution: 'resolved' | 'suggested' | 'unknown' | 'rejected'
  match_confidence: number
  reason: string
  suggestions: string[]
  requires_user_decision: boolean
  decision?: 'confirm' | 'reject' | 'substitute'
  substituteValue?: string
}

// --- Estado completo ---
interface RecipeState {
  // Estado
  ingredients: string[]
  orderId: string | null
  status: 'idle' | 'confirming' | 'processing' | 'done' | 'error'
  chips: Chip[]
  result: any | null
  error: string | null
  timeline: TimelineItem[]

  // Resoluções pendentes (para a tela de revisão)
  pendingResolutions: PendingResolution[]

  // Ações existentes
  addIngredient: (ingredient: string) => void
  removeIngredient: (index: number) => void
  setOrderId: (id: string) => void
  setChips: (chips: Chip[]) => void
  toggleChip: (index: number) => void
  setStatus: (status: RecipeState['status']) => void
  setResult: (result: any) => void
  setError: (error: string | null) => void
  reset: () => void

  // Timeline
  updateTimeline: (item: TimelineItem) => void
  resetTimeline: () => void

  // Resoluções
  setPendingResolutions: (resolutions: PendingResolution[]) => void
  updatePendingResolution: (originalInput: string, decision: 'confirm' | 'reject' | 'substitute', substituteValue?: string) => void
  clearPendingResolutions: () => void
  getConfirmedIngredients: () => string[]
}

export const useRecipeStore = create<RecipeState>((set, get) => ({
  // Estado inicial
  ingredients: [],
  orderId: null,
  status: 'idle',
  chips: [],
  result: null,
  error: null,
  timeline: [],
  pendingResolutions: [],

  // --- Ações existentes ---
  addIngredient: (ingredient) =>
    set((state) => ({
      ingredients: [...state.ingredients, ingredient],
    })),

  removeIngredient: (index) =>
    set((state) => ({
      ingredients: state.ingredients.filter((_, i) => i !== index),
    })),

  setOrderId: (id) => set({ orderId: id }),
  setChips: (chips) => set({ chips }),
  toggleChip: (index) =>
    set((state) => ({
      chips: state.chips.map((chip, i) =>
        i === index ? { ...chip, active: !chip.active } : chip
      ),
    })),

  setStatus: (status) => set({ status }),
  setResult: (result) => set({ result }),
  setError: (error) => set({ error }),

  reset: () =>
    set({
      ingredients: [],
      orderId: null,
      status: 'idle',
      chips: [],
      result: null,
      error: null,
      timeline: [],
      pendingResolutions: [],
    }),

  // --- Timeline ---
  updateTimeline: (item) =>
    set((state) => {
      const existingIndex = state.timeline.findIndex((t) => t.id === item.id)
      if (existingIndex >= 0) {
        const newTimeline = [...state.timeline]
        newTimeline[existingIndex] = item
        return { timeline: newTimeline }
      }
      return { timeline: [...state.timeline, item] }
    }),

  resetTimeline: () => set({ timeline: [] }),

  // --- Resoluções ---
  setPendingResolutions: (resolutions) => set({ pendingResolutions: resolutions }),

  updatePendingResolution: (originalInput, decision, substituteValue) =>
    set((state) => ({
      pendingResolutions: state.pendingResolutions.map((r) =>
        r.original_input === originalInput
          ? { ...r, decision, substituteValue }
          : r
      ),
    })),

  clearPendingResolutions: () => set({ pendingResolutions: [] }),

  getConfirmedIngredients: () => {
    const state = get()
    return state.pendingResolutions
      .filter((r) => r.decision === 'confirm' || (r.resolution === 'resolved' && !r.requires_user_decision))
      .map((r) => r.normalized_input || r.original_input)
  },
}))