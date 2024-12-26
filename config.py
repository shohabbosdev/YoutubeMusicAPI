from environs import Env
env=Env()
env.read_env()

key=env('key')
token=env('token')