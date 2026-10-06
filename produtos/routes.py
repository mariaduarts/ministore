from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_connection
import mysql.connector

produtos_bp = Blueprint('produtos', __name__, template_folder='templates')

@produtos_bp.route('/produtos')
def listar():
    conn = None
    cursor = None
    produtos = []
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        sql = '''
            SELECT p.*, c.nome AS categoria_nome 
            FROM produtos p 
            LEFT JOIN categorias c ON p.id_categoria = c.id 
            ORDER BY p.nome
        '''
        cursor.execute(sql)
        produtos = cursor.fetchall()
    except mysql.connector.Error as e:
        flash(f'Erro ao buscar produtos: {e}', 'danger')
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    return render_template('lista_produto.html', produtos=produtos)

@produtos_bp.route('/produtos/novo', methods=['GET', 'POST'])
def novo():
    conn = None
    cursor = None
    categorias = []
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM categorias ORDER BY nome')
        categorias = cursor.fetchall()

        if request.method == 'POST':
            codigo = request.form['codigo']
            nome = request.form['nome']
            descricao = request.form.get('descricao', '')
            preco = request.form['preco'].replace(',', '.')
            id_categoria = request.form.get('id_categoria') or None

            cursor.execute(
                '''INSERT INTO produtos (codigo, nome, descricao, preco, id_categoria) 
                   VALUES (%s, %s, %s, %s, %s)''',
                (codigo, nome, descricao, float(preco), id_categoria)
            )
            conn.commit()
            flash('Produto cadastrado com sucesso!', 'success')
            return redirect(url_for('produtos.listar'))
    except mysql.connector.Error as e:
        flash(f'Erro ao salvar produto: {e}', 'danger')
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return render_template('form_produto.html', produto=None, categorias=categorias)

@produtos_bp.route('/produtos/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == 'POST':
            codigo = request.form['codigo']
            nome = request.form['nome']
            descricao = request.form.get('descricao', '')
            preco = request.form['preco'].replace(',', '.')
            id_categoria = request.form.get('id_categoria') or None

            cursor.execute(
                '''UPDATE produtos 
                   SET codigo=%s, nome=%s, descricao=%s, preco=%s, id_categoria=%s 
                   WHERE id=%s''',
                (codigo, nome, descricao, float(preco), id_categoria, id)
            )
            conn.commit()
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('produtos.listar'))

        cursor.execute('SELECT * FROM produtos WHERE id = %s', (id,))
        produto = cursor.fetchone()

        cursor.execute('SELECT * FROM categorias ORDER BY nome')
        categorias = cursor.fetchall()

        if not produto:
            flash('Produto não encontrado.', 'danger')
            return redirect(url_for('produtos.listar'))

        return render_template('form_produto.html', produto=produto, categorias=categorias)
    except mysql.connector.Error as e:
        flash(f'Erro: {e}', 'danger')
        return redirect(url_for('produtos.listar'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@produtos_bp.route('/produtos/<int:id>/excluir', methods=['POST'])
def excluir(id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM produtos WHERE id = %s', (id,))
        conn.commit()
        flash('Produto excluído com sucesso!', 'success')
    except mysql.connector.Error as e:
        flash(f'Erro ao excluir produto: {e}', 'danger')
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    return redirect(url_for('produtos.listar'))