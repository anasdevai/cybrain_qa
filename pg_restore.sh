export PGPASSWORD='choose_a_strong_password'
pg_restore -U cybrain_user -d cybrain_db -h localhost /root/cybrain_backup.dump
