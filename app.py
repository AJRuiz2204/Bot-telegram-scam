from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import telegram
import logging
import pandas as pd
from io import BytesIO, StringIO  # Asegurarse de que ambas clases estén correctamente importadas
from zoneinfo import ZoneInfo

# Configura la salida de los registros para depuración
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Token del bot generado con BotFather
TOKEN = '7168942216:AAEvWeLDFvDnhfR4FjCTgrbT_qMKDMtjFus'
# IDs de usuario de Telegram para enviar mensajes privados
USER_IDS = [1179527859, 6739616550, 1526601639]

class BotCommands:
    def __init__(self, updater):
        self.updater = updater
        self.dp = self.updater.dispatcher
        self.messages = []  # Almacenar los mensajes con la información requerida
        self.register_handlers()

    def register_handlers(self):
        self.dp.add_handler(CommandHandler('start', self.start))
        self.dp.add_handler(CommandHandler('stop', self.stop))
        self.dp.add_handler(CommandHandler('comandos', self.comandos))
        self.dp.add_handler(CommandHandler('jornada', self.jornada))
        self.dp.add_handler(MessageHandler(Filters.text & (~Filters.command), self.filter_messages))

    def start(self, update: Update, context: CallbackContext):
        update.message.reply_text("Hola, soy tu bot de asistencia.")

    def comandos(self, update: Update, context: CallbackContext):
        commands = "/start - Inicia el bot\n"
        commands += "/stop - Detiene el bot\n"
        commands += "/comandos - Muestra la lista de comandos disponibles\n"
        commands += "/jornada - Exporta los registros de jornada a un archivo CSV"
        update.message.reply_text(commands)

    def filter_messages(self, update: Update, context: CallbackContext):
        message = update.message.text.lower()
        keywords = ['buenos días', 'buen día', 'presente en', 'iniciando labores', 'iniciando jornada',
                    'finalizando jornada', 'finaliza jornada', 'jornada finalizada', 'finalizando en', 'finalizando labores']
        if any(kw in message for kw in keywords):
            local_time = update.message.date.replace(tzinfo=ZoneInfo('UTC')).astimezone(ZoneInfo('America/El_Salvador'))
            formatted_time = local_time.strftime('%Y-%m-%d %H:%M:%S')
            self.messages.append({
                "usuario": update.message.from_user.full_name,
                "mensaje": update.message.text,
                "hora": formatted_time
            })
            for user_id in USER_IDS:
                context.bot.send_message(chat_id=user_id,
                                         text=f"Registro: {update.message.from_user.full_name} ha enviado: \n{update.message.text}",
                                         parse_mode=telegram.ParseMode.HTML)

    def jornada(self, update: Update, context: CallbackContext):
        try:
            format_type = update.message.text.split()[-1] if len(update.message.text.split()) > 1 else 'csv'
            df = pd.DataFrame(self.messages)
            if format_type.lower() == 'xlsx':
                output = BytesIO()
                df.to_excel(output, index=False)
                output.seek(0)
                context.bot.send_document(chat_id=update.effective_chat.id, document=output, filename='jornada.xlsx')
            else:
                output = StringIO()
                df.to_csv(output, index=False)
                output.seek(0)
                context.bot.send_document(chat_id=update.effective_chat.id, document=output, filename='jornada.csv')
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}")

    def stop(self, update: Update, context: CallbackContext):
        update.message.reply_text('Bot detenido.')
        context.bot.stop_polling()

def main():
    updater = Updater(token=TOKEN, use_context=True)
    bot_commands = BotCommands(updater)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
