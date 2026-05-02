"""
SISTEMA ERP - GESTÃO DE ATIVOS DE TI 
Desenvolvido por: Wesley Walter
Novidades: Soft Delete, Audit Trail, Importação em Lote, Gráficos BI e QR Code.
"""

import customtkinter as ctk
import sqlite3
import csv
import hashlib
import logging
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import qrcode
from PIL import Image
from tkinter import ttk, messagebox, filedialog

# Configuração de Logs
logging.basicConfig(filename='auditoria_sistema.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==========================================
# CAMADA DE BANCO DE DADOS (DATA LAYER)
# ==========================================
class DatabaseManager:
    def __init__(self, db_name='erp_estoque_v3.db'):
        self.db_name = db_name
        self._initialize_database()

    def _initialize_database(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Tabela de Usuários
            cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT)''')
            
            if cursor.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
                cursor.execute("INSERT INTO usuarios (username, password, role) VALUES (?, ?, ?)", 
                               ("admin", hashlib.sha256("admin123".encode()).hexdigest(), "Administrador"))

            # Tabela de Ativos (Agora com 'ativo' para Soft Delete)
            cursor.execute('''CREATE TABLE IF NOT EXISTS ativos (
                id INTEGER PRIMARY KEY AUTOINCREMENT, produto TEXT, modelo TEXT, serie TEXT UNIQUE, 
                status TEXT, departamento TEXT, responsavel TEXT, valor REAL, observacoes TEXT, 
                data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, ativo INTEGER DEFAULT 1)''')

            # Tabela de Histórico (Audit Trail)
            cursor.execute('''CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ativo_id INTEGER, usuario TEXT, 
                acao TEXT, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    def execute_query(self, query, params=(), fetch=False, get_lastrowid=False):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetch: return cursor.fetchall()
            conn.commit()
            if get_lastrowid: return cursor.lastrowid
            return cursor.rowcount

# ==========================================
# CAMADA DE INTERFACE E REGRAS
# ==========================================
class SistemaEstoqueTI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ERP Diretor - Gestão de Ativos")
        self.geometry("1300x850")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.db = DatabaseManager()
        self.usuario_logado = None
        self.cargo_logado = None
        self.exibir_tela_login()

    def _hash_senha(self, senha):
        return hashlib.sha256(senha.encode()).hexdigest()

    # --- TELA DE LOGIN ---
    def exibir_tela_login(self):
        self.login_frame = ctk.CTkFrame(self, width=400, height=500, corner_radius=15)
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self.login_frame, text="Acesso Restrito", font=("Arial", 22, "bold")).pack(pady=(40, 20))
        self.ent_user = ctk.CTkEntry(self.login_frame, width=250, placeholder_text="Usuário")
        self.ent_user.pack(pady=10)
        self.ent_pass = ctk.CTkEntry(self.login_frame, width=250, placeholder_text="Senha", show="*")
        self.ent_pass.pack(pady=10)

        ctk.CTkButton(self.login_frame, text="Acessar", width=250, command=self.autenticar).pack(pady=20)
        self.bind('<Return>', lambda e: self.autenticar())

    def autenticar(self):
        user = self.ent_user.get().strip()
        senha = self._hash_senha(self.ent_pass.get().strip())

        res = self.db.execute_query("SELECT username, role FROM usuarios WHERE username=? AND password=?", (user, senha), fetch=True)
        if res:
            self.usuario_logado, self.cargo_logado = res[0]
            logging.info(f"Login efetuado: {self.usuario_logado}")
            self.login_frame.destroy()
            self.unbind('<Return>')
            self.construir_dashboard()
        else:
            messagebox.showerror("Erro", "Acesso Negado")

    # --- DASHBOARD PRINCIPAL ---
    def construir_dashboard(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # SIDEBAR
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="💻 ESTOQUE TI", font=("Arial", 22, "bold")).pack(pady=30)

        if self.cargo_logado == "Administrador":
            ctk.CTkButton(self.sidebar, text="👤 Gestão de Usuários", command=self.abrir_gestao_usuarios, fg_color="#1f6aa5").pack(pady=5, padx=20)
            ctk.CTkButton(self.sidebar, text="📈 Painel BI (Gráficos)", command=self.mostrar_graficos, fg_color="#8E44AD").pack(pady=5, padx=20)
            ctk.CTkButton(self.sidebar, text="📥 Importar Planilha CSV", command=self.importar_csv, fg_color="#D35400").pack(pady=5, padx=20)
            
        ctk.CTkButton(self.sidebar, text="📊 Exportar Relatório", command=self.exportar_csv, fg_color="#2FA572").pack(pady=5, padx=20)
        ctk.CTkButton(self.sidebar, text="Sair do Sistema", command=self.logout, fg_color="#E74C3C").pack(side="bottom", pady=30, padx=20)

        # CONTAINER
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.container.grid_rowconfigure(3, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # KPIs
        self.cards = ctk.CTkFrame(self.container, fg_color="transparent")
        self.cards.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.cards.grid_columnconfigure((0, 1, 2), weight=1)
        self.lbl_estoque = self._criar_kpi(self.cards, "Em Estoque", "#3498DB", 0)
        self.lbl_uso = self._criar_kpi(self.cards, "Em Uso", "#2FA572", 1)
        self.lbl_alerta = self._criar_kpi(self.cards, "Manutenção", "#E74C3C", 2)

        # FORMULÁRIO
        self.form = ctk.CTkFrame(self.container)
        self.form.grid(row=1, column=0, sticky="ew", pady=(0, 20), ipadx=10, ipady=10)
        
        ctk.CTkLabel(self.form, text="Produto:").grid(row=0, column=0, padx=5, pady=5)
        self.in_prod = ctk.CTkEntry(self.form, width=130); self.in_prod.grid(row=0, column=1)
        ctk.CTkLabel(self.form, text="Modelo:").grid(row=0, column=2, padx=5, pady=5)
        self.in_mod = ctk.CTkEntry(self.form, width=130); self.in_mod.grid(row=0, column=3)
        ctk.CTkLabel(self.form, text="Valor (R$):").grid(row=0, column=4, padx=5, pady=5)
        self.in_val = ctk.CTkEntry(self.form, width=130); self.in_val.grid(row=0, column=5)

        ctk.CTkLabel(self.form, text="Status:").grid(row=1, column=0, padx=5, pady=5)
        self.in_status = ctk.CTkComboBox(self.form, values=["Estoque", "Em Uso", "Manutenção", "Vendido"], width=130)
        self.in_status.grid(row=1, column=1)
        ctk.CTkLabel(self.form, text="Depto:").grid(row=1, column=2, padx=5, pady=5)
        self.in_depto = ctk.CTkEntry(self.form, width=130); self.in_depto.grid(row=1, column=3)
        ctk.CTkLabel(self.form, text="Resp:").grid(row=1, column=4, padx=5, pady=5)
        self.in_resp = ctk.CTkEntry(self.form, width=130); self.in_resp.grid(row=1, column=5)

        ctk.CTkLabel(self.form, text="Séries:").grid(row=2, column=0, sticky="ne", pady=5)
        self.in_series = ctk.CTkTextbox(self.form, width=130, height=50); self.in_series.grid(row=2, column=1, pady=5)
        ctk.CTkLabel(self.form, text="Obs:").grid(row=2, column=2, sticky="ne", pady=5)
        self.in_obs = ctk.CTkTextbox(self.form, width=280, height=50); self.in_obs.grid(row=2, column=3, columnspan=3, pady=5, sticky="w")

        # BOTÕES AÇÃO
        box_btn = ctk.CTkFrame(self.form, fg_color="transparent")
        box_btn.grid(row=0, column=6, rowspan=3, padx=10)
        ctk.CTkButton(box_btn, text="💾 Cadastrar", command=self.salvar_ativos).pack(pady=2)
        self.btn_upd = ctk.CTkButton(box_btn, text="✏️ Atualizar", fg_color="#E67E22", command=self.atualizar_ativo)
        self.btn_upd.pack(pady=2)
        ctk.CTkButton(box_btn, text="🔳 Gerar QR Code", fg_color="#34495E", command=self.gerar_qr_code).pack(pady=2)

        # TABELA E FILTROS
        self.search = ctk.CTkEntry(self.container, placeholder_text="🔍 Busca Dinâmica...", width=400)
        self.search.grid(row=2, column=0, sticky="w", pady=(0,10))
        self.search.bind("<KeyRelease>", lambda e: self.carregar_dados())

        self.tree_frame = ctk.CTkFrame(self.container)
        self.tree_frame.grid(row=3, column=0, sticky="nsew")

        cols = ("ID", "Produto", "Modelo", "Nº Série", "Status", "Depto", "Responsável", "Valor")
        self.table = ttk.Treeview(self.tree_frame, columns=cols, show="headings")
        scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscroll=scroll.set)

        for col in cols: self.table.heading(col, text=col); self.table.column(col, width=100, anchor="center")
        self.table.column("ID", width=40)
        self.table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        
        # BARRA INFERIOR DE OPÇÕES
        bottom_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        bottom_frame.grid(row=4, column=0, sticky="ew", pady=10)
        
        ctk.CTkButton(bottom_frame, text="🕒 Ver Histórico do Item", fg_color="#7F8C8D", command=self.ver_historico).pack(side="left")
        
        if self.cargo_logado == "Administrador":
            ctk.CTkButton(bottom_frame, text="🗑️ Apagar (Soft Delete)", fg_color="#E74C3C", command=self.soft_delete).pack(side="right")
        else:
            self.btn_upd.configure(state="disabled")

        self.carregar_dados()

    def _criar_kpi(self, master, titulo, cor, col):
        f = ctk.CTkFrame(master, fg_color="#2b2b2b", corner_radius=10)
        f.grid(row=0, column=col, sticky="ew", padx=10)
        v = ctk.CTkLabel(f, text="0", font=("Arial", 30, "bold"), text_color=cor)
        v.pack(pady=(10, 0))
        ctk.CTkLabel(f, text=titulo).pack(pady=(0, 10))
        return v

    # --- REGRAS DE NEGÓCIO DA TABELA ---
    def carregar_dados(self):
        for i in self.table.get_children(): self.table.delete(i)
        
        termo = f"%{self.search.get()}%"
        query = "SELECT id, produto, modelo, serie, status, departamento, responsavel, valor FROM ativos WHERE ativo=1 AND (produto LIKE ? OR serie LIKE ? OR departamento LIKE ?)"
        for r in self.db.execute_query(query, (termo, termo, termo), fetch=True):
            row = list(r)
            if row[7]: row[7] = f"R$ {row[7]:.2f}"
            self.table.insert("", "end", values=row)
            
        self.lbl_estoque.configure(text=str(self.db.execute_query("SELECT COUNT(*) FROM ativos WHERE ativo=1 AND status='Estoque'", fetch=True)[0][0]))
        self.lbl_uso.configure(text=str(self.db.execute_query("SELECT COUNT(*) FROM ativos WHERE ativo=1 AND status='Em Uso'", fetch=True)[0][0]))
        self.lbl_alerta.configure(text=str(self.db.execute_query("SELECT COUNT(*) FROM ativos WHERE ativo=1 AND status='Manutenção'", fetch=True)[0][0]))

    def registrar_historico(self, ativo_id, acao):
        self.db.execute_query("INSERT INTO historico (ativo_id, usuario, acao) VALUES (?, ?, ?)", (ativo_id, self.usuario_logado, acao))

    def salvar_ativos(self):
        prod, mod = self.in_prod.get(), self.in_mod.get()
        val_str = self.in_val.get().replace(',', '.')
        series = [s.strip() for s in self.in_series.get("1.0", "end-1c").split('\n') if s.strip()]
        st, dp, rp, ob = self.in_status.get(), self.in_depto.get(), self.in_resp.get(), self.in_obs.get("1.0", "end-1c")

        if not prod or not series: return messagebox.showwarning("Aviso", "Produto e Série obrigatórios.")
        v = float(val_str) if val_str else 0.0

        inseridos = 0
        for s in series:
            try:
                ativo_id = self.db.execute_query(
                    "INSERT INTO ativos (produto, modelo, serie, status, departamento, responsavel, valor, observacoes) VALUES (?,?,?,?,?,?,?,?)",
                    (prod, mod, s, st, dp, rp, v, ob), get_lastrowid=True)
                self.registrar_historico(ativo_id, "CADASTRO INICIAL")
                inseridos += 1
            except: pass
            
        messagebox.showinfo("Cadastro", f"{inseridos} itens cadastrados com sucesso!")
        self.in_series.delete("1.0", "end")
        self.carregar_dados()

    def atualizar_ativo(self):
        sel = self.table.selection()
        if not sel: return
        item_id = self.table.item(sel[0], 'values')[0]
        st, dp, rp = self.in_status.get(), self.in_depto.get(), self.in_resp.get()
        
        self.db.execute_query("UPDATE ativos SET status=?, departamento=?, responsavel=? WHERE id=?", (st, dp, rp, item_id))
        self.registrar_historico(item_id, f"ATUALIZADO: Status p/ {st}, Depto p/ {dp}")
        self.carregar_dados()

    def soft_delete(self):
        sel = self.table.selection()
        if not sel: return
        if messagebox.askyesno("Soft Delete", "Ocultar permanentemente este item do sistema?"):
            item_id = self.table.item(sel[0], 'values')[0]
            self.db.execute_query("UPDATE ativos SET ativo=0 WHERE id=?", (item_id,))
            self.registrar_historico(item_id, "EXCLUSÃO LÓGICA (SOFT DELETE)")
            self.carregar_dados()

    def ver_historico(self):
        sel = self.table.selection()
        if not sel: return messagebox.showwarning("Aviso", "Selecione um ativo.")
        item_id = self.table.item(sel[0], 'values')[0]
        
        win = ctk.CTkToplevel(self)
        win.title(f"Audit Trail - Ativo #{item_id}")
        win.geometry("500x300")
        
        txt = ctk.CTkTextbox(win, width=480, height=280)
        txt.pack(padx=10, pady=10)
        
        hist = self.db.execute_query("SELECT data, usuario, acao FROM historico WHERE ativo_id=? ORDER BY data DESC", (item_id,), fetch=True)
        if not hist:
            txt.insert("end", "Nenhum histórico encontrado.")
        else:
            for h in hist:
                txt.insert("end", f"[{h[0]}] {h[1]} -> {h[2]}\n")
        txt.configure(state="disabled")

    def gerar_qr_code(self):
        sel = self.table.selection()
        if not sel: return messagebox.showwarning("Aviso", "Selecione um ativo na tabela.")
        serie = self.table.item(sel[0], 'values')[3] 
        
        qr = qrcode.make(f"ESTOQUE_TI_SERIE:{serie}")
        img_name = f"QR_{serie}.png"
        qr.save(img_name)
        messagebox.showinfo("QR Code Gerado", f"Salvo na raiz do aplicativo como: {img_name}")
        try: os.startfile(img_name) 
        except: pass

    def importar_csv(self):
        f = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not f: return
        
        try:
            with open(f, 'r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter=';')
                next(reader) 
                inseridos = 0
                for row in reader:
                    if len(row) >= 4: 
                        try:
                            a_id = self.db.execute_query("INSERT INTO ativos (produto, modelo, serie, status) VALUES (?,?,?,?)", 
                                                         (row[0], row[1], row[2], row[3]), get_lastrowid=True)
                            self.registrar_historico(a_id, "IMPORTAÇÃO EM LOTE")
                            inseridos += 1
                        except: pass
            messagebox.showinfo("Sucesso", f"{inseridos} itens importados da planilha!")
            self.carregar_dados()
        except Exception as e:
            messagebox.showerror("Erro", f"A planilha deve ser CSV separada por ponto-e-vírgula (;).\n{e}")

    def mostrar_graficos(self):
        win = ctk.CTkToplevel(self)
        win.title("Painel de Business Intelligence")
        win.geometry("600x500")
        
        estoque = self.db.execute_query("SELECT COUNT(*) FROM ativos WHERE ativo=1 AND status='Estoque'", fetch=True)[0][0]
        uso = self.db.execute_query("SELECT COUNT(*) FROM ativos WHERE ativo=1 AND status='Em Uso'", fetch=True)[0][0]
        manut = self.db.execute_query("SELECT COUNT(*) FROM ativos WHERE ativo=1 AND status='Manutenção'", fetch=True)[0][0]
        
        fig, ax = plt.subplots(figsize=(5, 4))
        labels = ['Estoque', 'Em Uso', 'Manutenção']
        sizes = [estoque, uso, manut]
        colors = ['#3498DB', '#2FA572', '#E74C3C']
        
        if sum(sizes) == 0:
            ax.text(0.5, 0.5, "Sem Dados para Exibir", ha='center', va='center')
        else:
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
            ax.axis('equal') 
        
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # --- FUNÇÕES ADMINISTRATIVAS COMPLETAS E INTEGRADAS ---
    def abrir_gestao_usuarios(self):
        win = ctk.CTkToplevel(self)
        win.title("IAM - Gestão de Acessos")
        win.geometry("400x450")
        win.attributes("-topmost", True)

        ctk.CTkLabel(win, text="Criar Novo Acesso", font=("Arial", 18, "bold")).pack(pady=20)
        ent_user = ctk.CTkEntry(win, placeholder_text="Username", width=250)
        ent_user.pack(pady=10)
        ent_pass = ctk.CTkEntry(win, placeholder_text="Senha Corporativa", show="*", width=250)
        ent_pass.pack(pady=10)
        combo_role = ctk.CTkComboBox(win, values=["Administrador", "Usuário Simples"], width=250)
        combo_role.pack(pady=10)
        combo_role.set("Usuário Simples")

        def executar_criacao():
            user, senha = ent_user.get().strip(), ent_pass.get().strip()
            if not user or not senha: 
                messagebox.showwarning("Aviso", "Preencha todos os campos!")
                return
            try:
                self.db.execute_query("INSERT INTO usuarios (username, password, role) VALUES (?,?,?)", 
                                      (user, self._hash_senha(senha), combo_role.get()))
                messagebox.showinfo("Sucesso", "Credencial provisionada com sucesso.")
                logging.info(f"Novo usuário '{user}' provisionado por {self.usuario_logado}.")
                win.destroy()
            except sqlite3.IntegrityError: 
                messagebox.showerror("Conflito", "Este username já está em uso.")
        
        ctk.CTkButton(win, text="Provisionar Credencial", command=executar_criacao).pack(pady=30)

    def exportar_csv(self):
        f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if f:
            # Exporta os dados, mas sem mostrar a coluna "ativo" oculta no relatorio 
            dados = self.db.execute_query("SELECT id, produto, modelo, serie, status, departamento, responsavel, valor, observacoes, data_registro FROM ativos WHERE ativo=1", fetch=True)
            try:
                with open(f, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file, delimiter=';')
                    writer.writerow(["ID", "Produto", "Modelo", "Série", "Status", "Depto", "Responsável", "Valor", "Observações", "Data/Hora Cadastro"])
                    writer.writerows(dados)
                logging.info(f"Relatório exportado com sucesso por {self.usuario_logado}.")
                messagebox.showinfo("Sucesso", "Relatório CSV gerado e exportado com sucesso.")
            except Exception as e:
                logging.error(f"Falha na exportação de CSV: {e}")
                messagebox.showerror("Erro", "Não foi possível gravar o arquivo.")

    def logout(self):
        for w in self.winfo_children(): w.destroy()
        self.usuario_logado = self.cargo_logado = None
        self.exibir_tela_login()

if __name__ == "__main__":
    app = SistemaEstoqueTI()
    app.mainloop()