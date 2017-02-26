# -*- coding: UTF-8 -*-
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
from smtplib import *
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formatdate
import os
from os.path import basename
from configparser import ConfigParser, Error as ConfigError
import time
from collections import OrderedDict


class NewsletterService(Frame):

    def __init__(self, master, max_retries, retry_delay, settings_file):
        Frame.__init__(self)
        self.master = master
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.settings_file = settings_file

        self.config = ConfigParser()
        self.selected_addresses = dict()
        self.all_selected = BooleanVar()
        self.attachement = None

        self.configure(background=color_petrol, padx=20, pady=5)
        self.init_widgets()
        self.load_addresses()

    def init_widgets(self):
        ### logo (top) ###
        self.logo_top = load_image('logo.png')
        Label(self, image=self.logo_top, bg=color_petrol).pack(pady=(10, 5))
        Label(self, font=h1, text="Newsletter Service", bg=color_petrol).pack(pady=(0, 10))

        ### input (text left + address list right) ###
        input_frame = Frame(self, bg=color_petrol)
        input_frame.pack(fill=BOTH, expand=True)

        # address list
        address_frame = Frame(input_frame, bg=color_petrol, width=250)
        address_frame.pack_propagate(False)  # feste groesse
        address_frame.pack(side=RIGHT, fill=Y)

        Label(address_frame, text="Email-Adressen", font=h2, bg=color_petrol).pack(pady=3, anchor=W)

        list_frame = LabelFrame(address_frame, bg=color_petrol, padx=5, pady=5)
        list_frame.pack(fill=BOTH, expand=True)
        canvas = Canvas(list_frame, background=color_petrol, highlightbackground=color_petrol)
        scrollbar = Scrollbar(list_frame, orient=VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.scroll_frame = Frame(canvas, background=color_petrol)  # frame for checkbuttons
        self.scroll_frame.pack(fill=BOTH, expand=True)
        canvas.create_window((0, 0), window=self.scroll_frame, anchor=NW)
        self.scroll_frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox(ALL)))  # reset scrollregion

        self.all_selected.set(True)
        Checkbutton(
                self.scroll_frame, text="  Alle Adressen auswählen",
                variable=self.all_selected,
                command=self.select_all_click,
                borderwidth=5,
                background=color_petrol,
                highlightbackground=color_petrol
        ).pack(anchor=W)

        # attachement
        Label(address_frame, text="Anhang", font=h2, bg=color_petrol).pack(pady=3, anchor=W)

        attachement_frame = LabelFrame(address_frame, bg=color_petrol, padx=5, pady=5)
        attachement_frame.pack(fill=BOTH, expand=True)

        self.attachement_image = load_image('attachement.png')
        self.attachement_button = Button(attachement_frame, image=self.attachement_image, command=self.attach_file, bg=color_petrol_light, cursor="hand2")
        self.attachement_button.pack(pady=(10, 0))
        self.attachement_file_label = Label(attachement_frame, relief=FLAT, wraplength=180, font=h2, bg=color_petrol)
        self.attachement_remove_image = load_image('delete.png')
        self.attachement_remove_button = Button(attachement_frame, image=self.attachement_remove_image, command=self.remove_attachement, activebackground=color_signal_light, bg=color_signal, cursor="hand2")

        # subject + message
        message_frame = Frame(input_frame, bg=color_petrol)
        message_frame.pack(side=LEFT, padx=(0, 50), fill=BOTH, expand=True)

        Label(message_frame, text="Betreff", font=h2, bg=color_petrol).pack(pady=3, anchor=W)
        self.subject_text = Text(message_frame, height=1, width=0, font=font, padx=5, pady=5)
        self.subject_text.pack(fill=X, pady=(0, 10))

        Label(message_frame, text="Nachricht", font=h2, bg=color_petrol).pack(pady=3, anchor=W)
        self.message_text = ScrolledText(message_frame, width=0, height=0, padx=5, pady=5)
        self.message_text.pack(side=LEFT, fill=BOTH, expand=True)

        # tab or enter to switch focus from subject field to message field
        def focus_message_text(event):
            self.message_text.focus()
            return "break"
        self.subject_text.bind('<Tab>', focus_message_text)
        self.subject_text.bind('<Return>', focus_message_text)

        ### send button / progressbar ###
        button_frame = Frame(self, bg=color_petrol)
        button_frame.pack(pady=(20, 0))
        self.send_button = Button(button_frame, text="Newsletter abschicken", command=self.send_mail, bg=color_petrol_light, font=h2, cursor="hand2")
        self.send_button.pack()
        self.progressbar = ttk.Progressbar(button_frame, orient='horizontal', mode='determinate', length=400)

        ### logo (bottom) ###
        self.logo_bottom = load_image('footer.png')
        Label(self, image=self.logo_bottom, bg=color_petrol).pack(pady=10)

    def select_all_click(self):
        is_selected = self.all_selected.get()
        for variable in self.selected_addresses.values():
            variable.set(is_selected)

    def attach_file(self):
        file_to_attach = filedialog.askopenfilename()
        if file_to_attach:
            self.attachement = file_to_attach
            self.attachement_button.pack_forget()
            self.attachement_file_label.config(text=basename(self.attachement))
            self.attachement_file_label.pack(side=LEFT)
            self.attachement_remove_button.pack(side=RIGHT)

    def remove_attachement(self):
        self.attachement = None
        self.attachement_file_label.pack_forget()
        self.attachement_remove_button.pack_forget()
        self.attachement_button.pack(pady=(10, 0))

    def load_addresses(self):
        # load addresses file location from .ini file
        self.config.read(self.settings_file)
        try:
            addresses_file = self.config.get('Database', 'file')
        except ConfigError as e:
            messagebox.showinfo("Fehler", "Es ist ein Fehler mit der Konfigurationsdatei aufgetreten: \n\n%s" % str(e))
            return

        # load addresses from file
        try:
            with open(addresses_file) as f:
                addresses = f.read().split()
            self.selected_addresses = OrderedDict((adresse, BooleanVar(value=True)) for adresse in addresses)
        except Exception as e:
            messagebox.showinfo("Fehler", "Die Email-Adressen konnten nicht gelesen werden: \n\n%s" % str(e))
            return

        # add addresses to list
        for address, variable in self.selected_addresses.items():
            Checkbutton(
                    self.scroll_frame,
                    text="  " + address,
                    variable=variable,
                    borderwidth=5,
                    background=color_petrol,
                    highlightbackground=color_petrol
            ).pack(anchor=W)

    def send_mail(self):
        # get email content
        recipients = [address for address, variable in self.selected_addresses.items() if variable.get()]
        if not recipients:
            messagebox.showinfo("Fehler", "Es wurden keine Empfänger ausgewählt.")
            return
        elif not messagebox.askyesno("Bestätigung", "Soll die Email an %s Empfänger abgeschickt werden?" % len(recipients)):
            return
        message = self.message_text.get(1.0, END)
        subject = self.subject_text.get(1.0, END)
        attachement = self.attachement

        # load mailserver, user and password from .ini file
        self.config.read(self.settings_file)
        try:
            server = self.config.get('SMTP', 'server')
            user = self.config.get('SMTP', 'user')
            password = self.config.get('SMTP', 'password')
            sender = self.config.get('SMTP', 'sender')
        except ConfigError as e:
            messagebox.showinfo("Fehler", "Es ist ein Fehler mit der Konfigurationsdatei aufgetreten: \n\n%s" % str(e))
            return

        # show progressbar
        self.send_button.pack_forget()
        self.progressbar.pack()
        self.progressbar.step(0)
        self.progressbar['maximum'] = len(recipients)
        window.update()

        # connect to mailserver
        smtp = SMTP()
        smtp.connect(server, 25)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        try:
            smtp.login(user, password)
        except SMTPAuthenticationError as e:
            self.send_button.pack()  # hide progressbar
            self.progressbar.pack_forget()
            messagebox.showinfo("Fehler", "Es ist ein Anmeldungsfehler aufgetreten: \n\n%s" % str(e))
            return

        # send email
        errors = dict()
        for recipient in recipients:
            email = MIMEMultipart()
            email['From'] = sender
            email['To'] = recipient
            email['Date'] = formatdate(localtime=True)
            email['Subject'] = Header(subject, "UTF-8")
            email.attach(MIMEText(message, 'plain', "UTF-8"))
            if attachement:
                with open(attachement, "rb") as f:
                    email.attach(MIMEApplication(
                        f.read(),
                        Content_Disposition='attachment; filename="%s"' % basename(attachement),
                        Name=basename(attachement)
                    ))

            retries = 1
            while True:  # allow retries
                try:
                    smtp.sendmail(sender, [recipient], email.as_string())
                except SMTPRecipientsRefused:
                    # recipient doesn't exist
                    errors[recipient] = "Empfänger ist nicht erreichbar und wurde daher übersprungen"
                except SMTPResponseException as e:
                    # error with status code
                    if retries <= self.max_retries and e.smtp_code == 450:  # 450 too much mail
                        time.sleep(self.retry_delay)
                        retries += 1
                        continue  # retry
                    else:
                        errors[recipient] = e.smtp_error
                except SMTPException as e:
                    # other error
                    errors[recipient] = str(e)
                break  # resume without retry

            # update progressbar
            self.progressbar.step()
            self.progressbar.update_idletasks()

        # hide progressbar
        self.send_button.pack()
        self.progressbar.pack_forget()

        if errors:
            # select failed recipients
            [variable.set(address in errors.keys()) for address, variable in self.selected_addresses.items()]

            # show error
            if len(recipients) == len(errors):
                # everything failed -> only show one error
                messagebox.showinfo("Fehler", "Die Emails konnten nicht versandt werden: \n\n%s" % errors.popitem()[1])
            else:
                error_messages = ["Fehler für %s: \n%s" % (recipient, error_message) for recipient, error_message in errors.items()]
                messagebox.showinfo("Information", "Einige Emails konnten nicht versandt werden."
                                    "Die betroffenen Empfänger sind in der Liste ausgewählt. \n\n%s" % '\n\n'.join(error_messages))
        else:
            # success
            messagebox.showinfo("Bestätigung", "Alle Emails erfolgreich verschickt!")

        smtp.quit()


def load_image(path):
    if getattr(sys, 'frozen', False):
        # in .exe file
        basedir = sys._MEIPASS
    else:
        # in python environment
        basedir = os.path.dirname(os.path.abspath(__file__))

    fullpath = os.path.join(basedir, 'images', path)
    return ImageTk.PhotoImage(Image.open(fullpath))


# Main
if __name__ == "__main__":
    color_petrol = "#2dcbba"
    color_signal = "#e74c3c"
    color_signal_light = "#ff7f6f"
    color_petrol_light = "#befff1"
    font = ("Times New Roman", 12)
    h1 = ("Times New Roman", 18)
    h2 = ("Times New Roman", 14)

    max_retries = 5
    retry_delay = 15  # seconds
    settings_file = 'settings.ini'

    # Window
    window = Tk()
    window.minsize(900, 700)
    window.wm_title("Newsletter für DieHundeB.A.R.F.")

    # Icon
    icon = load_image('mail.gif')
    window.tk.call('wm', 'iconphoto', window._w, icon)

    service = NewsletterService(window, max_retries, retry_delay, settings_file)
    service.pack(side="top", fill="both", expand=True)
    window.mainloop()
