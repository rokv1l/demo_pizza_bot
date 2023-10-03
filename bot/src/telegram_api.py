from telegram.ext import ApplicationBuilder

import config

app = ApplicationBuilder().token(config.token).build()
job_queue = app.job_queue
