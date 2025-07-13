# Testing-System

Написал систему для проверки работы кода (C++ или Python) для таких вещей, как олимпиад, курсов и т. д. и т. п. под хостинг TimeWeb. У меня она будет использоваться в школьном клубе. Дизайн нагло украден с моего основного сайта ([тык](https://infosecfamily.ru)).

## Архитектура

```
testingsystem/
├── public_html
│   ├── index.wsgi
│   ├── static
│   │   └── styles.css
│   ├── templates
│   │   ├── admin.html
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── login.html
│   │   └── task.html
│   ├── testlib.py
│   ├── uploads
│   └── users.py
├── requirements.txt
└── tmp_exec
```
## Запуск

Перед запуском вам необходимо сделать несколько вещей. В первую очередь создайте виртуальное окружение под python 3.10 ([см. здесь](https://timeweb.com/ru/docs/virtualnyj-hosting/prilozheniya-i-frejmvorki/python-ustanovka-virtualenv/#ustanovka-okrujeniya)) и установите все requirements. Далее проверьте все пути в [testlib.py](https://github.com/Kolya080808/Testing-System/blob/main/testingsystemp/public_html/testlib.py) и [index.wsgi](https://github.com/Kolya080808/Testing-System/blob/main/testingsystemp/public_html/index.wsgi) и замените на свои. Так же прошу заменить пользователей и пароли в [users.py](https://github.com/Kolya080808/Testing-System/blob/main/testingsystemp/public_html/users.py) и секретный код в [index.wsgi](https://github.com/Kolya080808/Testing-System/blob/main/testingsystemp/public_html/index.wsgi), так как я поставил первое что пришло в голову. Если вы будете менять задания (все задания в index.wsgi), то посмотрите и замените тесты. Далее вся система уже будет готова к запуску.

## Послесловие

### **Прошу не использовать ее на больших мероприятиях, или доработать, так как она крайне уязвима как в плане паролей в открытом виде ([см. users.py](https://github.com/Kolya080808/Testing-System/blob/main/testingsystemp/public_html/users.py)), так и в плане выполнения кода. Даже обычный `os.system("rm -rf /")` может сработать. Так что будьте осторожны.**

Ну, думаю на этом стоит закончить. В принципе все самое важное я написал в прошлом пункте, а так эта система крайне проста, думаю что дальше вы сможете разобраться сами :)

~~А если нет, открывайте issue или напишите мне в телеграмм, со всем помогу~~
