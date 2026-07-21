'use client'

import { CheckCircle, AlertCircle, XCircle, HelpCircle, Edit, Trash2 } from 'lucide-react'
import { motion } from 'framer-motion'

interface Resolution {
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

interface IngredientReviewProps {
  resolutions: Resolution[]
  onUpdate: (originalInput: string, decision: 'confirm' | 'reject' | 'substitute', substituteValue?: string) => void
  onContinue: () => void
}

export default function IngredientReview({ resolutions, onUpdate, onContinue }: IngredientReviewProps) {
  const resolved = resolutions.filter(r => r.resolution === 'resolved' && !r.requires_user_decision)
  const needsReview = resolutions.filter(r => r.requires_user_decision)

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-dark-wood">Revise a interpretação dos ingredientes</h2>

      {resolved.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-green-700 flex items-center gap-2">
            <CheckCircle size={18} /> Reconhecidos
          </h3>
          <div className="flex flex-wrap gap-2 mt-1">
            {resolved.map((r) => (
              <span key={r.original_input} className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                {r.normalized_input}
              </span>
            ))}
          </div>
        </div>
      )}

      {needsReview.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-amber-700 flex items-center gap-2">
            <AlertCircle size={18} /> Precisam de atenção
          </h3>
          <div className="space-y-3 mt-2">
            {needsReview.map((r) => (
              <div key={r.original_input} className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium">{r.original_input}</span>
                    {r.resolution === 'suggested' && r.suggestions.length > 0 && (
                      <span className="text-sm text-wood/70 ml-2">
                        → Você quis dizer <strong>{r.suggestions[0]}</strong>?
                      </span>
                    )}
                    {r.resolution === 'unknown' && (
                      <span className="text-sm text-wood/70 ml-2">Não conheço esse ingrediente.</span>
                    )}
                    {r.resolution === 'rejected' && (
                      <span className="text-sm text-red-600 ml-2">Não parece ser um ingrediente.</span>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => onUpdate(r.original_input, 'confirm')}
                      className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                    >
                      Confirmar
                    </button>
                    <button
                      onClick={() => onUpdate(r.original_input, 'reject')}
                      className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                    >
                      Remover
                    </button>
                    <button
                      onClick={() => {
                        const newValue = prompt('Digite o nome correto:', r.original_input)
                        if (newValue) onUpdate(r.original_input, 'substitute', newValue)
                      }}
                      className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Substituir
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <button
        onClick={onContinue}
        disabled={needsReview.some(r => !r.decision)}
        className="w-full py-3 bg-terracotta text-white rounded-lg font-medium hover:bg-terracotta/90 transition-colors disabled:opacity-50"
      >
        Continuar com estes ingredientes
      </button>
    </div>
  )
}