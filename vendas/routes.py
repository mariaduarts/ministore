from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_connection
import mysql.connector

vendas_bp = Blueprint('vendas', __name__, template_folder='templates')

@vendas_bp.route('/vendas')
def listar():
    conn = None
    cursor = None
    vendas = []
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        sql = '''
            SELECT v.*, c.nome AS cliente_nome 
            FROM vendas v 
            JOIN clientes c ON v.id_cliente = c.id 
            ORDER BY v.data_venda DESC
        '''
        cursor.execute(sql)
        vendas = cursor.fetchall()
    except mysql.connector.Error as e:
        flash(f'Erro ao buscar vendas: {e}', 'danger')
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    return render_template('lista_venda.html', vendas=vendas)

@vendas_bp.route('/vendas/novo', methods=['GET', 'POST'])
def novo():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == 'POST':
            id_cliente = request.form['id_cliente']
            id_produtos = request.form.getlist('id_produto[]')
            quantidades = request.form.getlist('quantidade[]')

            total_venda = 0
            itens_para_gravar = []

            for pid, qtd in zip(id_produtos, quantidades):
                if pid and qtd and int(qtd) > 0:
                    cursor.execute('SELECT preco FROM produtos WHERE id = %s', (pid,))
                    prod = cursor.fetchone()
                    if prod:
                        preco_unit = float(prod['preco'])
                        quantidade = int(qtd)
                        subtotal = preco_unit * quantidade
                        total_venda += subtotal
                        itens_para_gravar.append((pid, quantidade, preco_unit))

            if not itens_para_gravar:
                flash('Adicione ao menos um produto com quantidade válida.', 'warning')
            else:
                cursor.execute(
                    'INSERT INTO vendas (id_cliente, total) VALUES (%s, %s)',
                    (id_cliente, total_venda)
                )
                id_venda = cursor.lastrowid

                for pid, qtd, p_unit in itens_para_gravar:
                    cursor.execute(
                        '''INSERT INTO itens_venda (id_venda, id_produto, quantidade, preco_unitario) 
                           VALUES (%s, %s, %s, %s)''',
                        (id_venda, pid, qtd, p_unit)
                    )

                conn.commit()
                flash('Venda concluída com sucesso!', 'success')
                return redirect(url_for('vendas.listar'))

        cursor.execute('SELECT * FROM clientes ORDER BY nome')
        clientes = cursor.fetchall()

        cursor.execute('SELECT * FROM produtos ORDER BY nome')
        produtos = cursor.fetchall()

        return render_template('form_venda.html', clientes=clientes, produtos=produtos)

    except mysql.connector.Error as e:
        flash(f'Erro ao registrar venda: {e}', 'danger')
        return redirect(url_for('vendas.listar'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@vendas_bp.route('/vendas/<int:id>')
def detalhe(id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('''
            SELECT v.*, c.nome AS cliente_nome 
            FROM vendas v 
            JOIN clientes c ON v.id_cliente = c.id 
            WHERE v.id = %s
        ''', (id,))
        venda = cursor.fetchone()

        if not venda:
            flash('Venda não encontrada.', 'danger')
            return redirect(url_for('vendas.listar'))

        cursor.execute('''
            SELECT iv.*, p.nome AS produto_nome, p.codigo 
            FROM itens_venda iv 
            JOIN produtos p ON iv.id_produto = p.id 
            WHERE iv.id_venda = %s
        ''', (id,))
        itens = cursor.fetchall()

        return render_template('detalhe_venda.html', venda=venda, itens=itens)
    except mysql.connector.Error as e:
        flash(f'Erro: {e}', 'danger')
        return redirect(url_for('vendas.listar'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()