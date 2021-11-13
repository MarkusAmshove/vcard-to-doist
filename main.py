import argparse
import vobject
from dateutil.parser import parse
from todoist.api import TodoistAPI

class Contact:

    def __init__(self, name, bday):
        self.name = name
        self.bday = bday

    def pretty_print(self):
        print(vars(self))

    def format_date(self):
        return self.bday.strftime('%d %B')

def read_contacts(filepath):
    with open(filepath) as f:
        vcard = vobject.readComponents(f.read())
        contacts = []
        for vc in vcard:
            if hasattr(vc, 'bday'):
                if hasattr(vc, 'n'):
                    bday_text = vc.bday.value
                    bday = parse(bday_text)
                    contact = Contact(f"{vc.n.value.given} {vc.n.value.family}", bday)
                    contacts.append(contact)
        return contacts

def find_project_id(api, projectname):
    for project in api.projects.all():
        if project['name'] == projectname:
            return project['id']
    raise Exception(f"Project with name {projectname} could not be found")

def find_item(api, projectid, name):
    items = api.projects.get_data(projectid)['items']
    for item in items:
        if name in item['content']:
            return item['id']

    return None

def sync_tasks(apikey, projectname, contacts):
    api = TodoistAPI(apikey)
    api.sync()
    project_id = find_project_id(api, projectname)

    print(f"Found project {projectname} with id {project_id}")

    actions_done = 0
    for contact in contacts:
        if actions_done >= 60:
            api.commit()
            actions_done = 0

        due_date = {"string": f"every {contact.format_date()}", "lang": "en", "is_recurring": True}
        item_id = find_item(api, project_id, contact.name)

        if item_id is None:
            api.items.add(f"{contact.name} gratulieren", project_id=project_id, due=due_date)
        else:
            item = api.items.get_by_id(item_id)
            item.update(due=due_date)

        actions_done = actions_done + 1

    api.commit()


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('projectname', type=str, help="Todoist Project name to put reminders in")
    argparser.add_argument('file', type=str, help="Path to vcard file")
    argparser.add_argument('apikey', type=str, help="Todoist API Key")
    args = argparser.parse_args()

    contacts = read_contacts(args.file)
    sync_tasks(args.apikey, args.projectname, contacts)

