#!/usr/bin/env python3

import json
import requests
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def delete_child_account(childAcctId, header, apiKey, apiSecret):
    deleteURL = "https://api-msp.dome9.com/msp/v2/account/" + childAcctId
    response = requests.delete(deleteURL, headers=header, auth=(apiKey, apiSecret))
    print("Delete response = " + str(response.status_code))
    return response

def create_ent_account(awsAcctID, header, apiKey, apiSecret):

    tenantEmailAddress = "aws-CGPMowner" + awsAcctID + "@mailsac.com"
#    tenantEmailAddress = "aws-CGPMowner" + awsAcctID + "@cpevent.info"

    payload = {
        "trustMspAccount": True,
        "licensingInfo": {
            "complianceEnabled": {
                "value": True
            },
            "enterpriseEnabled": {
                "value": True
            },
            "allowedUsers": {
                "value": None
            },
            "networkEnabled": {
                "value": True
            },
            "iamsafeEnabled": {
                "value": True
            },
            "fimEnabled": {
                "value": False
            }
        },
        "adminFirstName": "Student",
        "pointOfContact": "jeffreyk@checkpoint.com",
        "adminLastName": "Learner",
        "companyName": "AWS-Corp"+awsAcctID,
        "parentAccountId": "107221",

        "adminEmail": tenantEmailAddress,
        "planName": "Enterprise"
    }

    response = requests.post("https://api-msp.dome9.com/msp/v2/account", data=json.dumps(payload), headers = header, auth=(apiKey, apiSecret))

    try:
        accountId = str(response.json()["accountId"])
        print("Account ID: " + accountId)
        print("MSP Tenant created with owner: " + tenantEmailAddress)

        return accountId, tenantEmailAddress

    except:
        print("Problem creating new account, due to: " + response.text)
        return response.text, tenantEmailAddress

def get_ent_token(accountId, header, apiKey, apiSecret):

    payload = {
        "roleName": "Super User",
        "accountId": accountId
    }

    response = requests.post("https://api.dome9.com/v2/auth/assume-role/jwt", data = json.dumps(payload), headers = header, auth=(apiKey, apiSecret))

    try:
        entAcctToken = response.json()["token"]
        print("Tenant Token: " + entAcctToken)

        return entAcctToken
    except:
        print("Problem getting tenant Token, due to: " + response.text)
        return response.text

def enable_ent_sso(headers, sso_data):
    #3 enable_ent_sso(entAccountToken) --> gen_ent_sso_data()

    requests.put("https://secure.dome9.com/api/account/sso", data = json.dumps(sso_data) , headers = headers)

def get_role(header):
    #4 adminRoleId = get_role(entAccountToken)

    adminRoles =  requests.get("https://api.dome9.com/v2/Role", headers= header)

    # cycle through returned dict for names=Super User, then return that ID
    # https://supportcenter.checkpoint.com/supportcenter/portal?eventSubmit_doGoviewsolutiondetails=&solutionid=sk147835

    try:
        return [obj for obj in adminRoles.json() if obj['name'] == "Super User"][0]["id"]
    except:
        print ("Couldn't find admin Role")
        return "456123"

def add_new_admin(header, awsAcctId):
#5 add_new_admin(entAccountToken)

    studentEmail = "aws-admin-" + awsAcctId + "@mailsac.com"
#    studentEmail = "aws-admin-" + awsAcctId + "@cpevent.info"

    payload = {
        "email": studentEmail,
        "firstName": "Student",
        "lastName": "KopkoAdmin",
        "ssoEnabled": False
    }

    response = requests.post("https://api.dome9.com/v2/user", data = json.dumps(payload), headers = header )

    try:
        newAdminId = str(response.json()["id"])
        print("New student admin created with ID: " + newAdminId)
        print("Login username: " + studentEmail)
        return newAdminId, studentEmail
    except:
        print("couldn't create student admin")
        return "987654", studentEmail

def modify_admin(header, adminRoleId, newAdminId):
    #6 modify_admin permissions)

    payload = {
        "roleIds": [adminRoleId],
        "permissions": {
            "access": [],
            "view": [],
            "manage": [],
            "crossAccountAccess": [],
            "create": []
        }
    }

    URL = "https://api.dome9.com/v2/user/" + newAdminId

    try:
        r = requests.put(URL, data = json.dumps(payload), headers = header)
        print ("Modify admin response: " + str(r.status_code))
        print (r.text)
    except Exception as e:
        logging.error('Exception: %s' % e, exc_info=True)
        logger.info("AWS Account Not Onboarded!!!")
  
 #7 onboard_aws_account()
 
def onboard_aws_account(awsAcctId, header):

    payload = {
        "name":"AWS-Corp"+awsAcctId,
        "credentials": {
            "arn": "arn:aws:iam::" + awsAcctId + ":role/domeServiceRole",
            "secret": "12345678",
            "type":"RoleBased"
        },
        "fullProtection": False,
        "allowReadOnly": True
    }

    try:
        r = requests.post("https://api.dome9.com/v2/CloudAccounts", data = json.dumps(payload), headers = header)
        print ("Onboard AWS response: " + str(r.status_code))
        print (r.text)
    except Exception as e:
        logging.error('Exception: %s' % e, exc_info=True)
        logger.info("AWS Account Not Onboarded!!!")


def sg_full_protect(sgId, header):
    payload = {"protectionMode": "FullManage"}

    url = "https://api.dome9.com/v2/CloudSecurityGroup/" + sgId + "/Protection-Mode"
    try:
        #this uses a the parent tenant level API token
        r = requests.post( url, data=json.dumps(payload), headers=header)
        if r.status_code == 201:
            print("Successfully Set SG Tamper Protection")
        else:
            print("Problem setting SG Tamper Protection")
        return r.status_code
    except:
        print("Unable to Set Tamper Protection ")
        return 999

def checkAssessment(assmntId, header):
    url = "https://api.dome9.com/v2/AssessmentHistoryv2/" + assmntId

    try:
        assessment = requests.get(url, headers=header)
        if assessment.status_code == 200:
            print("Found the assessment")

            a1 = assessment.json()

            region = a1["request"]["region"]
            # looking for 'us_east_1'
            print(region)
            assmntName = a1["request"]["name"]
            # looking for 'AWS CIS Foundations v. 1.2.0'
            print(assmntName)
            passedTests = a1["stats"]["passed"]
            # looking for >21
            print (str(passedTests))

            if region == "us_east_1" and assmntName == "AWS CIS Foundations v. 1.2.0" and passedTests > 21:
                return "platinum"
            else:
                return "green"
        else:
            print("Couldn't find the assesment")
            return "red"
    except Exception as e:
        logging.error('Exception: %s' % e, exc_info=True)
        print("Something went wrong looking for the assessment")
        return "red"


def checkFinding(findingId, header):
    url = "https://api.dome9.com/v2/Compliance/Finding/" + findingId

    try:
        finding = requests.get(url, headers = header)
        if finding.status_code == 200:
            print("Finding is valid!")
            fdict = json.loads(finding.content)

            if fdict["entityType"] == "KubernetesDeployment":
                if fdict["origin"] == "ContainersRuntimeProtection":
                    return "RuntimeFindingPassed"
                #Double check this value when Threat Intel is enabled
                elif  fdict["origin"] == "Intelligence":
                    return "ThreatIntelPassed"
            else:
                return "FoundAlert"
        else:
            print("Finding is invalid!")
            return "AlertNotFound"
    except:
        print("Something went wrong looking for the Alert ID/finding")
        return "AlertNotFound"

def searchFindingForIntelligence(header):
    url = "https://api.dome9.com/v2/Compliance/Finding/search"

    body = {
        "pageSize": 500,
        "sorting": {
            "fieldName": "createdTime",
            "direction": -1
        },
        "filter": {
            "fields": [
                {
                    "name": "organizationalUnitId",
                    "value": "00000000-0000-0000-0000-000000000000"
                },
                {
                    "name": "alertType",
                    "value": "0"
                }
            ]
        }
    }

    try:
        findinglist = requests.post(url, headers=header, params=body)

        flistdict = json.loads(findinglist.content)

        for finding in flistdict["findings"]:
            if finding["origin"] == "Magellan":
                if finding["cloudAccountType"] == "Kubernetes":
                    print("ThreatIntelPassed")
                    return "ThreatIntelPassed"

        print("ThreatIntelNotFound")
        return "ThreatIntelNotFound"
    except:
        print("Something went wrong searching through  findings")
        return "AlertNotFound"

def checkAssets(header):
    url = "https://api.dome9.com/v2/protected-asset/search"

    try:
        r = requests.post(url, headers=header)

        rdict = json.loads(r.content)

        #Expect over 100 assets after onboarding EKS Cluster
        if rdict['totalCount'] >= 100:
            return True
        else:
            return False

    except Exception as e:
        print("Something went wrong looking for Assets")

def checkK8sAdmissionControl(header):
    url = "https://api.dome9.com/v2/kubernetes/admissionControl/policy"
    try:
        r = requests.get(url, headers=header)

        rdict = json.loads(r.content)

        #Check if prevention is set on policy
        if rdict[0]['action'] == "Prevention":
            return True
        else:
            return False

    except Exception as e:
        print("Something went wrong checking AdmissionControl")

def checkK8sAssessment(assmntId, header):
    url = "https://api.dome9.com/v2/AssessmentHistoryv2/" + assmntId

    try:
        assessment = requests.get(url, headers=header)
        if assessment.status_code == 200:
            print("Found the assessment")

            a1 = assessment.json()

            assmntName = a1["request"]["name"]
            # looking for "CIS Amazon Elastic Kubernetes Service (EKS) Benchmark v1.0.1"
            print("Assessment Name: " + assmntName)
            passedTests = a1["stats"]["passed"]
            # looking for >21
            print ("Passed Tests: " + str(passedTests))

            if assmntName == "CIS Amazon Elastic Kubernetes Service (EKS) Benchmark v1.0.1" and passedTests > 14:
                return "platinum"
            else:
                return "green"
        else:
            print("Couldn't find the assesment")
            return "red"
    except Exception as e:
        logging.error('Exception: %s' % e, exc_info=True)
        print("Something went wrong looking for the assessment")
        return "red"

def getPwResetUrl(key, mailbox):
    url = "https://mailsac.com/api/addresses/" + mailbox + "/messages"
    header = {
        "Mailsac-Key" : key
    }
    try:

        mailbox = (requests.get(url, headers=header)).json()

        #check the whole mailbox to get the welcome message mail
        for mail in mailbox:
            if mail["subject"] == "Welcome to CloudGuard Dome9":
                for link in mail["links"]:
                    if link.startswith("https://secure.dome9.com/v2/reset-password?requestId="):
                        print(link)
                        return link

        message = "Something went wrong getting CloudGuard Password Reset.  Try CloudGuard Password Reset Manually on CloudGuard Login screen and then visit https://mailsac.com/inbox/" + mailbox + " to get the reset Link"
        print(message)
        return message

    except Exception as e:
        logging.error('Exception: %s' % e, exc_info=True)
        message = "Something went wrong getting CloudGuard Password Reset.  Try CloudGuard Password Reset Manually on CloudGuard Login screen and then visit https://mailsac.com/inbox/" + mailbox + " to get the reset Link"
        print(message)
        return message