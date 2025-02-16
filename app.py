import os
import paramiko
import time
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class BuscaConfig:
    def __init__(self):
        credenciais = os.getenv("AUTOMATION_CREDENTIALS")
        self.usuario, self.senha = credenciais.split(':', 1)

    def busca_startup_config(self, ip_dispositivo):
        print(f"Buscando startup-config do dispositivo {ip_dispositivo}")

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            paramiko.Transport._preferred_ciphers = ['aes256-cbc', 'aes192-cbc', 'aes128-cbc', '3des-cbc']
            ssh.connect(
                hostname=ip_dispositivo,
                username=self.usuario,
                password=self.senha,
                look_for_keys=False,
                allow_agent=False
            )

            stdin, stdout, stderr = ssh.exec_command("show startup-config")
            output = stdout.read().decode('utf-8')
            erro = stderr.read().decode('utf-8')

            if erro:
                configCompleta = f"Erro ao executar o comando: {erro}"
            else:
                configCompleta = output

            ssh.close()
            return configCompleta

        except Exception as e:
            return f"Erro ao conectar ou executar o comando: {str(e)}"
        
    def aplica_config(self, ip_dispositivo, config_sugerida):
        print(f"Aplicando configuração sugerida pela IA no dispositivo {ip_dispositivo}")

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            paramiko.Transport._preferred_ciphers = ['aes256-cbc', 'aes192-cbc', 'aes128-cbc', '3des-cbc']

            ssh.connect(
                hostname=ip_dispositivo,
                username=self.usuario,
                password=self.senha,
                look_for_keys=False,
                allow_agent=False
            )

            shell = ssh.invoke_shell()
            shell.send("configure terminal\n")
            time.sleep(1)

            for comando in config_sugerida.split("\n"):
                if comando.strip():
                    shell.send(comando + "\n")
                    time.sleep(0.5)

            shell.send("end\n")
            shell.send("write memory\n")
            time.sleep(2)

            output = shell.recv(65535).decode('utf-8')
            ssh.close()
            return output

        except Exception as e:
            return f"Erro ao conectar ou executar o comando: {str(e)}"

class AIGENAPI:
    def __init__(self):
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self.prompt1 = os.getenv("PROMPT_1")
        self.prompt2 = os.getenv("PROMPT_2")

        self.generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
        }

        self.modelo = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        generation_config=self.generation_config,
        )

    def busca_sugestao(self, config_cisco):
        print("Buscando sugestão completa de melhoria através da IA")
        
        sessao_chat = self.modelo.start_chat(
        history=[
        ]
        )

        resposta = sessao_chat.send_message(f"{self.prompt1}{config_cisco}")

        return resposta.text
    
    def config_sugerida(self, config_cisco):
        print("Buscando configuração sugerida através da IA")
        sessao_chat = self.modelo.start_chat(
        history=[
        ]
        )

        resposta = sessao_chat.send_message(f"{self.prompt2}{config_cisco}")

        return resposta.text

if __name__ == "__main__":
    ip_dispositivo = os.getenv("IP_DEVICE")
    os.makedirs("output", exist_ok=True)

    config = BuscaConfig()
    configCompleta = config.busca_startup_config(ip_dispositivo)
    with open(f"output/startup-config_pre_melhoria.txt", "w", encoding="utf-8") as file:
        file.write(configCompleta)

    ia_func = AIGENAPI()
    sugestaoCompleta = ia_func.busca_sugestao(configCompleta)
    with open(f"output/sugestao_completa.txt", "w", encoding="utf-8") as file:
        file.write(sugestaoCompleta)
    
    print(f"Sugestão completa de melhoria salva no arquivo sugestao_completa.txt")
