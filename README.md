# 💻 ERP Inventory - Gestão Corporativa de Ativos de TI

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-blue?style=for-the-badge)
![GitHub repo size](https://img.shields.io/github/repo-size/WesleyWalterDev/erp-estoque-ti?style=for-the-badge)

Um sistema completo de nível corporativo (ERP) desenvolvido em Python para o controle, movimentação e auditoria de ativos de infraestrutura de TI. 

Focado em segurança, rastreabilidade e eficiência, o sistema foi arquitetado com boas práticas de Engenharia de Software (Clean Code) para resolver problemas reais de gestão de patrimônio em multinacionais e grandes empresas.

---

## 🚀 Funcionalidades Principais (Nível Enterprise)

* **🔒 RBAC (Role-Based Access Control):** Sistema de login seguro com senhas criptografadas (SHA-256) e hierarquia de permissões (Administrador vs. Usuário Operacional).
* **🕵️‍♂️ Audit Trail (Trilha de Auditoria):** O sistema registra e exibe um histórico completo de quem cadastrou, moveu ou excluiu cada ativo, garantindo 100% de rastreabilidade temporal.
* **🛡️ Soft Delete (Exclusão Lógica):** Equipamentos não são apagados permanentemente do banco de dados para evitar perda de dados forenses, sendo apenas inativados da interface do usuário.
* **📈 Painel de BI Integrado:** Geração de gráficos visuais dinâmicos em tempo real integrados à interface (via Matplotlib) para tomada de decisão gerencial.
* **🔲 Geração de QR Code:** Integração com hardware físico através da geração automática de etiquetas QR Code com os números de série dos equipamentos para colar nas máquinas.
* **📥/📤 Importação e Exportação em Lote:** Permite alimentar o banco de dados rapidamente processando planilhas `.csv` (Data Ingestion) e exportar relatórios formatados.
* **📝 Logs de Sistema:** Auditoria silenciosa em background (via biblioteca `logging`) registrando todos os acessos e eventuais falhas do sistema em um arquivo `.log`.

---

## 📸 Demonstração do Sistema

> **Nota para os visitantes:** A interface foi construída em Dark Mode nativo para redução de fadiga visual, padrão em ferramentas de infraestrutura.

---

## 🛠️ Tecnologias e Bibliotecas Utilizadas

* **Linguagem:** Python 3.x
* **Interface Gráfica (GUI):** `customtkinter`
* **Banco de Dados:** `sqlite3` (Local e seguro)
* **Segurança:** `hashlib` (Criptografia)
* **Data & Analytics:** `matplotlib`, `csv`
* **Integração Física:** `qrcode`, `Pillow`

---

## 🏗️ Arquitetura e Boas Práticas

Este projeto foi construído pensando em escalabilidade e facilidade de manutenção:
1. **Separação de Responsabilidades (MVC-like):** Camada de banco de dados (`DatabaseManager`) abstraída da camada de interface e regras de negócio.
2. **Context Managers (`with`):** Prevenção de vazamento de memória e corrupção de banco de dados no gerenciamento de conexões SQLite.
3. **Tratamento Avançado de Exceções (`try/except`):** O aplicativo intercepta violações de integridade (ex: cadastro de número de série duplicado) sem crashar a aplicação.

---

## ⚙️ Como Executar o Projeto na sua Máquina

1. Clone este repositório:
   ```bash
   git clone [https://github.com/WesleyWalterDev/erp-estoque-ti.git](https://github.com/WesleyWalterDev/erp-estoque-ti.git)