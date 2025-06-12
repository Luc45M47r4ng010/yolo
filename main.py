import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import cv2
from detect import detectar_placa_e_ocr, buscar_no_historico
import os
import csv
from datetime import datetime

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Reconhecimento de Placas de Veículos")
        self.geometry("1000x800")
        self.configure(bg="#f0f0f0")
        
        # Variáveis de controle
        self.cap = None
        self.video_running = False
        self.after_id = None
        
        self.criar_widgets()
        self.criar_menu()
        
    def criar_widgets(self):
        # Frame principal
        main_frame = tk.Frame(self, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame de controles
        control_frame = tk.Frame(main_frame, bg="#f0f0f0")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Botões
        self.btn_imagem = tk.Button(
            control_frame, 
            text="Selecionar Imagem", 
            command=self.escolher_imagem,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white"
        )
        self.btn_imagem.pack(side=tk.LEFT, padx=5)
        
        self.btn_video = tk.Button(
            control_frame, 
            text="Abrir Vídeo", 
            command=self.escolher_video,
            font=("Arial", 12),
            bg="#2196F3",
            fg="white"
        )
        self.btn_video.pack(side=tk.LEFT, padx=5)
        
        self.btn_camera = tk.Button(
            control_frame, 
            text="Usar Câmera", 
            command=self.usar_camera,
            font=("Arial", 12),
            bg="#FF9800",
            fg="white"
        )
        self.btn_camera.pack(side=tk.LEFT, padx=5)
        
        self.btn_parar = tk.Button(
            control_frame, 
            text="Parar Vídeo", 
            command=self.parar_video,
            font=("Arial", 12),
            bg="#F44336",
            fg="white",
            state=tk.DISABLED
        )
        self.btn_parar.pack(side=tk.LEFT, padx=5)
        
        # Painel de exibição
        self.painel = tk.Label(main_frame, bg="black")
        self.painel.pack(fill=tk.BOTH, expand=True)
        
        # Frame de resultados
        result_frame = tk.Frame(main_frame, bg="#f0f0f0")
        result_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Resultados de detecção
        tk.Label(
            result_frame, 
            text="Placas Detectadas:", 
            font=("Arial", 12, "bold"),
            bg="#f0f0f0"
        ).pack(anchor=tk.W)
        
        self.resultado_texto = tk.StringVar()
        self.resultado_label = tk.Label(
            result_frame, 
            textvariable=self.resultado_texto, 
            font=("Arial", 12), 
            justify=tk.LEFT,
            bg="#f0f0f0"
        )
        self.resultado_label.pack(fill=tk.X)
        
        # Frame de busca
        search_frame = tk.Frame(main_frame, bg="#f0f0f0")
        search_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(
            search_frame, 
            text="Buscar Placa:", 
            font=("Arial", 12, "bold"),
            bg="#f0f0f0"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.entrada_busca = tk.Entry(
            search_frame, 
            font=("Arial", 12),
            width=20
        )
        self.entrada_busca.pack(side=tk.LEFT, padx=5)
        
        self.btn_buscar = tk.Button(
            search_frame, 
            text="Buscar", 
            command=self.buscar_placa,
            font=("Arial", 12),
            bg="#607D8B",
            fg="white"
        )
        self.btn_buscar.pack(side=tk.LEFT, padx=5)
        
        # Treeview para histórico
        self.hist_tree = ttk.Treeview(
            main_frame,
            columns=("Placa", "Data/Hora"),
            show="headings",
            height=5
        )
        self.hist_tree.heading("Placa", text="Placa")
        self.hist_tree.heading("Data/Hora", text="Data/Hora")
        self.hist_tree.column("Placa", width=150)
        self.hist_tree.column("Data/Hora", width=200)
        self.hist_tree.pack(fill=tk.X, pady=(10, 0))
        
    def criar_menu(self):
        menubar = tk.Menu(self)
        
        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Abrir Imagem", command=self.escolher_imagem)
        file_menu.add_command(label="Abrir Vídeo", command=self.escolher_video)
        file_menu.add_command(label="Usar Câmera", command=self.usar_camera)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.quit)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        
        # Menu Histórico
        hist_menu = tk.Menu(menubar, tearoff=0)
        hist_menu.add_command(label="Exibir Histórico Completo", command=self.exibir_historico_completo)
        hist_menu.add_command(label="Limpar Histórico", command=self.limpar_historico)
        menubar.add_cascade(label="Histórico", menu=hist_menu)
        
        self.config(menu=menubar)
    
    def escolher_imagem(self):
        self.parar_video()
        caminho = filedialog.askopenfilename(filetypes=[("Imagens", "*.jpg *.png *.jpeg")])
        if not caminho:
            return
        
        try:
            imagem_resultado, placas = detectar_placa_e_ocr(caminho)
            self.exibir_imagem(imagem_resultado)
            
            placas_texto = "Placas encontradas:\n" + "\n".join([p[0] for p in placas]) if placas else "Nenhuma placa detectada"
            self.resultado_texto.set(placas_texto)
            self.atualizar_historico()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar imagem: {str(e)}")
    
    def escolher_video(self):
        self.parar_video()
        caminho = filedialog.askopenfilename(filetypes=[("Vídeos", "*.mp4 *.avi *.mov")])
        if not caminho:
            return
        
        try:
            self.cap = cv2.VideoCapture(caminho)
            self.video_running = True
            self.btn_parar.config(state=tk.NORMAL)
            self.processar_video()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir vídeo: {str(e)}")
    
    def usar_camera(self):
        self.parar_video()
        try:
            self.cap = cv2.VideoCapture(0)  # 0 para câmera padrão
            if not self.cap.isOpened():
                raise Exception("Não foi possível acessar a câmera")
            
            self.video_running = True
            self.btn_parar.config(state=tk.NORMAL)
            self.processar_video()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao acessar câmera: {str(e)}")
    
    def parar_video(self):
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.video_running = False
        self.btn_parar.config(state=tk.DISABLED)
    
    def processar_video(self):
        if not self.video_running or not self.cap:
            return
        
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.resize(frame, (800, 600))
            frame_resultado, placas = detectar_placa_e_ocr(frame, is_video_frame=True)
            self.exibir_imagem(frame_resultado)
            
            placas_texto = "Placas detectadas (vídeo):\n" + "\n".join([p[0] for p in placas]) if placas else "Nenhuma placa detectada"
            self.resultado_texto.set(placas_texto)
        
        self.after_id = self.after(10, self.processar_video)
    
    def exibir_imagem(self, imagem_cv2):
        imagem_rgb = cv2.cvtColor(imagem_cv2, cv2.COLOR_BGR2RGB)
        imagem_pil = Image.fromarray(imagem_rgb)
        
        # Redimensionar mantendo aspect ratio
        largura_painel = self.painel.winfo_width()
        altura_painel = self.painel.winfo_height()
        
        if largura_painel > 1 and altura_painel > 1:  # Evita redimensionamento inicial
            ratio = min(largura_painel/imagem_pil.width, altura_painel/imagem_pil.height)
            nova_largura = int(imagem_pil.width * ratio)
            nova_altura = int(imagem_pil.height * ratio)
            imagem_pil = imagem_pil.resize((nova_largura, nova_altura), Image.LANCZOS)
        
        imagem_tk = ImageTk.PhotoImage(imagem_pil)
        self.painel.configure(image=imagem_tk)
        self.painel.image = imagem_tk
    
    def buscar_placa(self):
        termo = self.entrada_busca.get().strip()
        if not termo:
            messagebox.showwarning("Aviso", "Digite um termo para busca")
            return
        
        resultados = buscar_no_historico(termo)
        if not resultados:
            messagebox.showinfo("Busca", "Nenhum resultado encontrado")
            return
        
        # Limpa a treeview
        for item in self.hist_tree.get_children():
            self.hist_tree.delete(item)
        
        # Adiciona os resultados
        for placa, data_hora in resultados:
            self.hist_tree.insert("", tk.END, values=(placa, data_hora))
    
    def exibir_historico_completo(self):
        resultados = buscar_no_historico("")
        if not resultados:
            messagebox.showinfo("Histórico", "O histórico está vazio")
            return
        
        # Limpa a treeview
        for item in self.hist_tree.get_children():
            self.hist_tree.delete(item)
        
        # Adiciona todos os resultados
        for placa, data_hora in resultados:
            self.hist_tree.insert("", tk.END, values=(placa, data_hora))
    
    def limpar_historico(self):
        if not os.path.exists("historico.csv"):
            return
        
        if messagebox.askyesno("Confirmar", "Deseja realmente limpar todo o histórico?"):
            try:
                os.remove("historico.csv")
                for item in self.hist_tree.get_children():
                    self.hist_tree.delete(item)
                messagebox.showinfo("Sucesso", "Histórico limpo com sucesso")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao limpar histórico: {str(e)}")
    
    def atualizar_historico(self):
        if os.path.exists("historico.csv"):
            self.exibir_historico_completo()

if __name__ == "__main__":
    app = Application()
    app.mainloop()