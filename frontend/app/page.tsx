'use client'

import { useState } from 'react'
import { useRecipeStore } from '@/store/recipeStore'
import { createOrder, confirmOrder, getResult } from '@/services/api'
import { toast } from 'sonner'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, X, Loader2, CheckCircle, Circle, AlertCircle } from 'lucide-react'
import { useWebSocket } from '@/hooks/useWebSocket'
import IngredientReview from '@/components/IngredientReview'

export default function Home() {
  const {
    ingredients,
    addIngredient,
    removeIngredient,
    orderId,
    chips,
    status,
    result,
    error,
    pendingResolutions,
    setOrderId,
    setChips,
    toggleChip,
    setStatus,
    setResult,
    setError,
    setPendingResolutions,
    updatePendingResolution,
    clearPendingResolutions,
    getConfirmedIngredients,
    reset,
  } = useRecipeStore()

  const timeline = useRecipeStore((state) => state.timeline)

  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [confirmLoading, setConfirmLoading] = useState(false)

  useWebSocket(orderId)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim()) {
      addIngredient(input.trim())
      setInput('')
    }
  }

  const handleGenerate = async () => {
    if (ingredients.length === 0) {
      toast.error('Adicione pelo menos um ingrediente')
      return
    }

    setLoading(true)
    setStatus('processing')
    setError(null)
    clearPendingResolutions()

    try {
      const message = `Quero uma receita com ${ingredients.join(', ')}`
      const orderData = await createOrder(message)

      if (orderData.status === 'interrupted') {
        // Se o backend retornou erro (validador ou specialist bloqueou)
        if (orderData.error) {
          setError(orderData.error)
          setStatus('error')
          toast.error(orderData.error)
          setLoading(false)
          return
        }

        // Se há resoluções pendentes, exibe a tela de revisão
        if (orderData.pending_resolutions && orderData.pending_resolutions.length > 0) {
          setOrderId(orderData.order_id)
          setPendingResolutions(orderData.pending_resolutions)
          setStatus('confirming')  // usamos o mesmo status, mas a UI vai renderizar IngredientReview
          toast.info('Revise a interpretação dos ingredientes')
          setLoading(false)
          return
        }

        // Fallback: chips tradicionais (sem pending_resolutions)
        setOrderId(orderData.order_id)
        const chipsFromIntentions = orderData.intentions.map((i: any, idx: number) => ({
          id: `intent_${idx}`,
          label: i.value,
          active: true,
          type: i.type,
        }))
        setChips(chipsFromIntentions)
        setStatus('confirming')
        toast.info('Confirme os ingredientes')
        setLoading(false)
        return
      }

      toast.error('Fluxo inesperado')
      setStatus('idle')
      setLoading(false)
    } catch (err: any) {
      console.error('❌ Erro detalhado:', err)
      const msg = err.message || 'Erro ao gerar receita'
      setError(msg)
      setStatus('error')
      toast.error(msg)
      setLoading(false)
    }
  }

  const handleConfirm = async () => {
    if (!orderId) return
    setConfirmLoading(true)
    setStatus('processing')
    setError(null)

    try {
      const activeChips = chips.filter(c => c.active).map(c => ({
        id: c.id,
        label: c.label,
        active: true,
      }))

      const confirmData = await confirmOrder(orderId, activeChips)

      if (confirmData.status === 'completed') {
        const resultData = await getResult(orderId)
        setResult(resultData)
        setStatus('done')
        toast.success('Receita pronta! 🍽️')
      } else {
        toast.error('Erro ao processar')
        setStatus('idle')
      }
    } catch (err: any) {
      const msg = err.message || 'Erro na confirmação'
      setError(msg)
      setStatus('error')
      toast.error(msg)
    } finally {
      setConfirmLoading(false)
    }
  }

  // Nova função para continuar após a revisão de ingredientes
  const handleContinueAfterReview = async () => {
    const confirmedIngredients = getConfirmedIngredients()
    if (confirmedIngredients.length === 0) {
      toast.error('Nenhum ingrediente confirmado')
      return
    }

    if (!orderId) {
      toast.error('Pedido não encontrado')
      return
    }

    setConfirmLoading(true)
    setStatus('processing')
    setError(null)

    try {
      // Usamos o mesmo endpoint de confirmação, enviando os ingredientes confirmados como chips
      const chips = confirmedIngredients.map((label, idx) => ({
        id: `intent_${idx}`,
        label: label,
        active: true,
      }))

      const confirmData = await confirmOrder(orderId, chips)

      if (confirmData.status === 'completed') {
        const resultData = await getResult(orderId)
        setResult(resultData)
        setStatus('done')
        clearPendingResolutions()
        toast.success('Receita pronta! 🍽️')
      } else {
        toast.error('Erro ao processar')
        setStatus('idle')
      }
    } catch (err: any) {
      const msg = err.message || 'Erro ao continuar'
      setError(msg)
      setStatus('error')
      toast.error(msg)
    } finally {
      setConfirmLoading(false)
    }
  }

  const handleNewRecipe = () => {
    reset()
    setInput('')
    setStatus('idle')
    setError(null)
    clearPendingResolutions()
    toast.success('Pronto para uma nova receita!')
  }

  const renderContent = () => {
    // Estado de erro
    if (status === 'error') {
      return (
        <div className="space-y-6">
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700 space-y-3">
            <div className="flex items-center gap-3">
              <AlertCircle size={24} className="text-red-500" />
              <h3 className="font-semibold text-lg">Ops! Algo deu errado</h3>
            </div>
            <p className="text-sm text-red-600">{error || 'Erro desconhecido'}</p>
          </div>
          <button
            onClick={handleNewRecipe}
            className="w-full py-3 bg-terracotta text-white rounded-lg font-medium hover:bg-terracotta/90 transition-colors"
          >
            Tentar novamente
          </button>
        </div>
      )
    }

    // Estado idle (formulário)
    if (status === 'idle') {
      return (
        <div className="space-y-6">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold text-dark-wood">
              Transforme ingredientes em receitas inteligentes
            </h1>
            <p className="text-wood/60">
              Adicione os itens e deixe a IA criar o prato perfeito.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Adicione um ingrediente..."
              className="flex-1 px-4 py-2.5 rounded-lg border border-wood/20 bg-white/50 focus:outline-none focus:ring-2 focus:ring-terracotta/40"
            />
            <button
              type="submit"
              className="p-2.5 bg-terracotta text-white rounded-lg hover:bg-terracotta/90 transition-colors"
            >
              <Plus size={20} />
            </button>
          </form>

          <div className="flex flex-wrap gap-2 min-h-[40px]">
            <AnimatePresence>
              {ingredients.map((item, idx) => (
                <motion.span
                  key={idx}
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.8, opacity: 0 }}
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-terracotta/10 text-terracotta rounded-full text-sm font-medium"
                >
                  {item}
                  <button
                    onClick={() => removeIngredient(idx)}
                    className="ml-1 hover:bg-terracotta/20 rounded-full p-0.5 transition-colors"
                  >
                    <X size={14} />
                  </button>
                </motion.span>
              ))}
            </AnimatePresence>
          </div>

          <button
            onClick={handleGenerate}
            disabled={ingredients.length === 0 || loading}
            className="w-full py-3 bg-terracotta text-white rounded-lg font-medium hover:bg-terracotta/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? <Loader2 className="animate-spin mx-auto" size={20} /> : '🚀 Gerar Receita'}
          </button>
        </div>
      )
    }

    // Estado confirming: se houver pendingResolutions, exibe IngredientReview
    if (status === 'confirming') {
      if (pendingResolutions && pendingResolutions.length > 0) {
        return (
          <IngredientReview
            resolutions={pendingResolutions}
            onUpdate={updatePendingResolution}
            onContinue={handleContinueAfterReview}
            loading={confirmLoading}
          />
        )
      }

      // Fallback: tela de confirmação tradicional (chips)
      return (
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-dark-wood">Confirme os ingredientes</h2>
          <div className="flex flex-wrap gap-2">
            {chips.map((chip, idx) => (
              <button
                key={chip.id}
                onClick={() => toggleChip(idx)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  chip.active
                    ? 'bg-terracotta text-white'
                    : 'bg-wood/10 text-wood/50 line-through'
                }`}
              >
                {chip.label}
              </button>
            ))}
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleConfirm}
              disabled={confirmLoading || chips.every(c => !c.active)}
              className="flex-1 py-3 bg-terracotta text-white rounded-lg font-medium hover:bg-terracotta/90 transition-colors disabled:opacity-50"
            >
              {confirmLoading ? <Loader2 className="animate-spin mx-auto" size={20} /> : '✅ Confirmar'}
            </button>
            <button
              onClick={handleNewRecipe}
              className="py-3 px-6 border border-wood/20 rounded-lg hover:bg-wood/5 transition-colors"
            >
              Cancelar
            </button>
          </div>
        </div>
      )
    }

    // Processing
    if (status === 'processing') {
      return (
        <div className="space-y-6">
          <h3 className="font-medium text-wood/70">Preparando sua receita...</h3>
          <div className="space-y-2">
            {timeline.length === 0 ? (
              <p className="text-sm text-wood/50">Iniciando...</p>
            ) : (
              timeline.map((item) => (
                <div key={item.id} className="flex items-center gap-3 text-sm">
                  {item.status === 'done' && <CheckCircle size={18} className="text-green-600" />}
                  {item.status === 'running' && <Loader2 size={18} className="animate-spin text-terracotta" />}
                  {item.status === 'pending' && <Circle size={18} className="text-wood/30" />}
                  <span className={item.status === 'done' ? 'text-wood/80' : 'text-wood/60'}>
                    {item.label}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      )
    }

    // Done
    if (status === 'done' && result) {
      const proposal = result.proposal || result.result || 'Receita não disponível'
      return (
        <div className="space-y-6">
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-wood/10 p-6 space-y-4">
            <pre className="whitespace-pre-wrap text-sm text-dark-wood font-sans">
              {proposal}
            </pre>
          </div>
          <button
            onClick={handleNewRecipe}
            className="w-full py-3 bg-terracotta text-white rounded-lg font-medium hover:bg-terracotta/90 transition-colors"
          >
            Nova receita
          </button>
        </div>
      )
    }

    return null
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between px-6 py-4 border-b border-wood/10">
        <div className="flex items-center gap-2">
          <span className="text-2xl font-bold tracking-tight text-terracotta">Chef IA</span>
          <span className="text-sm text-wood/60">v2</span>
        </div>
      </header>

      <main className="flex-1 container max-w-4xl mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          {renderContent()}
        </div>
      </main>
    </div>
  )
}