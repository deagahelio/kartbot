# kartbot

Bot do Discord pro servidor SRB2Kart-Brasil.

## Dependências

- Python 3.8+ (+ `discord.py`, `psutil`)
- `screen`
- `stuff`

## Uso

- Copie o arquivo `kartbot_config.template.json` para `kartbot_config.json` e defina os valores apropriados
- Inicie o servidor usando `screen -dmS server /caminho/do/srb2kart -dedicated &`
- Execute `python3.8 kartbot.py`

## Configuração

- `prefix` - Prefixo usado para os comandos do bot
- `description` - Descrição do bot que aparece no comando de ajuda
- `token` - Token do bot


- `screen_name` - Nome do `screen` do servidor
- `server_folder_path` - Caminho da pasta do servidor **com uma barra (/) no final!**
- `server_executable_name` - Nome do arquivo executável do servidor
- `server_executable_args` - Argumentos passados ao servidor (deixe o `-dedicated`)
- `server_max_players` - Número máximo de jogadores do servidor (não influencia a funcionalidade do bot, é apenas exibido no `k!info`)
- `ip_message` - Mensagem a ser exibida no `k!ip`
- `permission_error_message` - Mensagem a ser exibida no `k!race` e `k!battle` quando o usuário não tiver o cargo necessário
- `helper_roles` - Lista de cargos que tem permissão aos [comandos de Helper](#helper)
- `admin_roles` - Lista de cargos que tem permissão aos [comandos de Admin](#admin)


- `enable_dkartconfig_corruption_workaround` - Quando habilitado, o bot copia o arquivo em `backup_dkartconfig_path` para `dkartconfig_path` quando `k!restart` é utilizado, para evitar a corrupção do arquivo
- `backup_dkartconfig_path` - Leia acima
- `dkartconfig_path` - Leia acima

## Comandos

- `k!help` - Exibe uma lista de comandos
- `k!ip` - Manda o IP do servidor
- `k!status|info|players` - Manda informações sobre o servidor e os jogadores conectados

### Helper

- `k!race` - Muda o gamemode para race
- `k!battle` - Muda o gamemode para battle

### Admin

- `k!restart` - Reinicia o servidor
- `k!command|comando <comando>` - Executa um comando

