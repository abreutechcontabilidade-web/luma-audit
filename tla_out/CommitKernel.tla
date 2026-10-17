---------------------------- MODULE CommitKernel ----------------------------
EXTENDS Naturals, TLC
CONSTANTS Acao, Valor, Limite
VARIABLES estado, risco, aprovado

Init == /\ estado = "inicial"
         /\ risco = 0
         /\ aprovado = FALSE

AcoesValidas == {
    [acao |-> "ajustar_brilho", min |-> 0.0, max |-> 100.0],
    [acao |-> "ajustar_gamma", min |-> 0.5, max |-> 1.6],
    [acao |-> "transferir_mb", min |-> 0.0, max |-> 500.0],
}

Inv_ValorAprovado == aprovado => \E a \in AcoesValidas :
    /\ a.acao = estado
    /\ risco >= a.min /\ risco <= a.max

Inv_RiscoNaoNegativo == risco >= 0

Commit(acao, valor) == 
    /\ \E a \in AcoesValidas : a.acao = acao
    /\ estado' = acao
    /\ risco' = valor
    /\ aprovado' = (valor >= 0)

Next == \E acao \in {"ajustar_brilho"}, valor \in 0..100 : Commit(acao, valor)
Spec == Init /\ [][Next]_<<estado, risco, aprovado>>
=============================================================================