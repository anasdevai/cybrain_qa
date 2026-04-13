sudo -u postgres psql -c "CREATE USER cybrain_user WITH PASSWORD 'choose_a_strong_password';"
sudo -u postgres psql -c "CREATE DATABASE cybrain_db OWNER cybrain_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cybrain_db TO cybrain_user;"
