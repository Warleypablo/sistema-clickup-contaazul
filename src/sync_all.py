#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal para sincronização de dados do Conta Azul
Executa todos os scripts de sincronização em sequência
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Importar os módulos de sincronização
from sync_vendas import ContaAzulVendasSync
from sync_produtos import ContaAzulProdutosSync
from sync_servicos import ContaAzulServicosSync
from sync_notas_fiscais import ContaAzulNotasFiscaisSync

def main():
    """Função principal para executar todas as sincronizações"""
    print("="*60)
    print("SINCRONIZAÇÃO CONTA AZUL - INICIANDO")
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*60)
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Verificar se o token de acesso está configurado
    if not os.getenv('CONTA_AZUL_ACCESS_TOKEN'):
        print("❌ ERRO: Token de acesso do Conta Azul não configurado!")
        print("Configure a variável CONTA_AZUL_ACCESS_TOKEN no arquivo .env")
        return False
    
    # Lista de sincronizações a executar
    sincronizacoes = [
        ("Produtos", ContaAzulProdutosSync),
        ("Serviços", ContaAzulServicosSync),
        ("Vendas", ContaAzulVendasSync),
        ("Notas Fiscais", ContaAzulNotasFiscaisSync)
    ]
    
    resultados = []
    
    for nome, classe_sync in sincronizacoes:
        print(f"\n🔄 Iniciando sincronização de {nome}...")
        try:
            sync_instance = classe_sync()
            
            # Executar apenas o método específico de cada classe
            if nome == "Produtos":
                sync_instance.sync_produtos()
            elif nome == "Serviços":
                sync_instance.sync_servicos()
            elif nome == "Vendas":
                sync_instance.sync_vendas()
            elif nome == "Notas Fiscais":
                sync_instance.sync_notas_fiscais()
            
            print(f"✅ {nome} sincronizado com sucesso!")
            resultados.append((nome, True, None))
            
        except Exception as e:
            print(f"❌ Erro na sincronização de {nome}: {str(e)}")
            resultados.append((nome, False, str(e)))
    
    # Relatório final
    print("\n" + "="*60)
    print("RELATÓRIO FINAL DA SINCRONIZAÇÃO")
    print("="*60)
    
    sucessos = 0
    falhas = 0
    
    for nome, sucesso, erro in resultados:
        if sucesso:
            print(f"✅ {nome}: Sucesso")
            sucessos += 1
        else:
            print(f"❌ {nome}: Falha - {erro}")
            falhas += 1
    
    print(f"\nResumo: {sucessos} sucessos, {falhas} falhas")
    print(f"Finalizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    return falhas == 0

def sync_individual(tipo):
    """Executa sincronização individual por tipo"""
    load_dotenv()
    
    if not os.getenv('CONTA_AZUL_ACCESS_TOKEN'):
        print("❌ ERRO: Token de acesso do Conta Azul não configurado!")
        return False
    
    tipo = tipo.lower()
    
    try:
        if tipo == 'vendas':
            sync = ContaAzulVendasSync()
            sync.sync_vendas()
        elif tipo == 'produtos':
            sync = ContaAzulProdutosSync()
            sync.sync_produtos()
        elif tipo == 'servicos':
            sync = ContaAzulServicosSync()
            sync.sync_servicos()
        elif tipo == 'notas_fiscais' or tipo == 'nf':
            sync = ContaAzulNotasFiscaisSync()
            sync.sync_notas_fiscais()
        else:
            print(f"❌ Tipo '{tipo}' não reconhecido.")
            print("Tipos disponíveis: vendas, produtos, servicos, notas_fiscais")
            return False
        
        print(f"✅ Sincronização de {tipo} concluída!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na sincronização de {tipo}: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Execução individual
        tipo = sys.argv[1]
        sync_individual(tipo)
    else:
        # Execução completa
        main()