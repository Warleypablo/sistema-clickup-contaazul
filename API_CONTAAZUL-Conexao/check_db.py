#!/usr/bin/env python3
"""
Script para verificar e criar tabelas no banco de dados
Use este script após o deploy no Render para verificar se as tabelas existem
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def check_database():
    try:
        # Conectar ao banco usando DATABASE_URL (Render) ou variáveis individuais (local)
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
            # Render/Heroku style
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            conn = psycopg2.connect(database_url)
        else:
            # Local development
            conn = psycopg2.connect(
                host=os.getenv("PG_HOST"),
                dbname=os.getenv("PG_DBNAME"),
                user=os.getenv("PG_USER"),
                password=os.getenv("PG_PASSWORD"),
                port=os.getenv("PG_PORT", 5432)
            )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verificar se as tabelas existem
        tables_to_check = ['clientes_turbo', 'a_receber_turbo', 'clientes_clickup']
        
        print("🔍 Verificando tabelas no banco de dados...")
        
        for table in tables_to_check:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table,))
            
            exists = cursor.fetchone()['exists']
            status = "✅ Existe" if exists else "❌ Não existe"
            print(f"Tabela '{table}': {status}")
            
            if exists:
                # Contar registros
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                print(f"  └── Registros: {count}")
        
        print("\n📊 Informações da conexão:")
        cursor.execute("SELECT version()")
        version = cursor.fetchone()['version']
        print(f"PostgreSQL: {version}")
        
        cursor.execute("SELECT current_database()")
        db_name = cursor.fetchone()['current_database']
        print(f"Banco atual: {db_name}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Verificação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao verificar banco de dados: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Verificador de Banco de Dados - Sistema ClickUp + Conta Azul")
    print("=" * 60)
    check_database()