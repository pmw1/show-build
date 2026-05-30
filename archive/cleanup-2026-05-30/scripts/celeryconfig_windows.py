broker_url = 'redis://:showbuild2025@192.168.51.223:6379/0'
result_backend = 'redis://:showbuild2025@192.168.51.223:6379/0'

task_routes = {
    'services.ffmpeg_tasks.*': {'queue': 'media'}
}

worker_prefetch_multiplier = 1
task_acks_late = True
task_reject_on_worker_lost = True
worker_max_tasks_per_child = 10

task_soft_time_limit = 3600
task_time_limit = 3900
result_expires = 3600

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True
