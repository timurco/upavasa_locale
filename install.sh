APP_NAME=upavasabot
#https://www.cloudsigma.com/how-to-configure-automatic-deployment-with-git-with-a-vps/
#sudo mkdir /ver/repo
#sudo mkdir /ver/repo/$APP_NAME.git
#sudo git init --bare /ver/repo/$APP_NAME.git
mv $APP_NAME.service /lib/systemd/system/$APP_NAME.service