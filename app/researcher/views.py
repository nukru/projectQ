# -*- coding: utf-8 -*-

from flask import Blueprint, request, url_for, flash, redirect, abort, send_file
from flask import render_template, g
from forms import SurveyForm, EditConsentForm, SectionForm, QuestionForm
from app.models import Survey, Consent, Section, StateSurvey, Answer
from app.models import Question, QuestionChoice, QuestionNumerical, QuestionText
from app.models import QuestionYN, QuestionLikertScale
from app import app, db
from app.decorators import researcher_required, belong_researcher
from flask.ext.login import login_user, logout_user, current_user, login_required
import tempfile
from werkzeug import secure_filename
from . import blueprint
import csv


@blueprint.route('/')
@blueprint.route('/index')
@login_required
@researcher_required
def index():
    surveys = Survey.query.filter(Survey.researcher==g.user).order_by(Survey.created.desc())
    return render_template('/researcher/index.html',
        tittle = 'Survey',
        surveys = surveys)

@login_required
@researcher_required
@blueprint.route('/survey/new', methods = ['GET', 'POST'])
def new():
    form = SurveyForm()
    if form.validate_on_submit():
        # file = request.files['file']
        # if file:
        filename = secure_filename(form.surveyXml.data.filename)
        if filename:
            tf = tempfile.NamedTemporaryFile()
            form.surveyXml.data.save(tf.name)
            msg = Survey.from_xml(tf.name, g.user)
            tf.close()
            for m in msg:
                flash(m)
            return redirect(url_for('researcher.index'))
        else:
            survey = Survey( title = form.title.data,
                description = form.description.data,
                endDate = form.endDate.data,
                startDate = None,
                maxNumberRespondents = form.maxNumberRespondents.data,
                duration = form.duration.data,
                researcher = g.user)
            db.session.add(survey)
            db.session.commit()
            flash('Your survey have been saved.')
        return redirect(url_for('researcher.editSurvey',id_survey = survey.id))
    return render_template('/researcher/new.html',
        title = 'New survey',
        form = form)


@login_required
@researcher_required
@blueprint.route('/survey/<int:id_survey>', methods = ['GET', 'POST'])
@belong_researcher('survey')
def editSurvey(id_survey):
    #get survey
    survey = Survey.query.get(id_survey)
    sections = survey.sections.all()
    form = SurveyForm()
    if form.validate_on_submit():
        survey.title = form.title.data
        survey.description = form.description.data
        survey.startDate = form.startDate.data
        survey.endDate = form.endDate.data
        survey.maxNumberRespondents = form.maxNumberRespondents.data
        survey.duration = form.duration.data
        db.session.add(survey)
        db.session.commit()
        flash('Your changes have been saved.')
    elif request.method != "POST":
        form.title.data = survey.title
        form.description.data = survey.description
        form.startDate.data = survey.startDate
        form.endDate.data = survey.endDate
        form.maxNumberRespondents.data = survey.maxNumberRespondents
        form.duration.data = survey.duration
    return render_template('/researcher/editSurvey.html',
        title = survey.title,
        form = form,
        survey = survey,
        sections = sections)

@login_required
@researcher_required
@blueprint.route('/survey/deleteSurvey/<int:id_survey>')
@belong_researcher('survey')
def deleteSurvey(id_survey):
    survey = Survey.query.get(id_survey)
    db.session.delete(survey)
    db.session.commit()
    flash('Survey removed')
    return redirect(url_for('researcher.index'))

@login_required
@researcher_required
@blueprint.route('/survey/exportSurvey/<int:id_survey>')
@belong_researcher('survey')
def exportSurvey(id_survey):
    '''http://stackoverflow.com/questions/14614756/how-can-i-generate-file-on-the-fly-and-delete-it-after-download
        http://stackoverflow.com/questions/13344538/how-to-clean-up-temporary-file-used-with-send-file/
    '''
    survey = Survey.query.get(id_survey)
    xml = survey.to_xml()
    tf = tempfile.NamedTemporaryFile()
    xml.write(tf.name,encoding="ISO-8859-1", method="xml")
    flash('Survey exported')
    return send_file(tf, as_attachment=True, attachment_filename=survey.title+'.xml')

def tips_path(section=None):
    '''Return a list with the path of a section
    '''
    l=[]
    if section is not None:
        l.append((section.title, section.id))
        while (section.parent is not None):
            l.append((section.parent.title, section.parent.id))
            section = section.parent
    l.reverse()
    return l


@login_required
@researcher_required
@blueprint.route('/survey/<int:id_survey>/consent/add', methods = ['GET', 'POST'])
@belong_researcher('survey')
def addConsent(id_survey):
    form = EditConsentForm()
    survey = Survey.query.get(id_survey)
    consents = survey.consents.all()
    
    if form.validate_on_submit():
        consent = Consent(text = form.text.data,
            survey = survey)
        db.session.add(consent)
        db.session.commit()
        flash('Adding consent.')
        return redirect(url_for('researcher.addConsent',id_survey = survey.id))
 
    return render_template('/researcher/consents.html',
        title = "consent",
        form = form,
        id_survey = id_survey,
        consents = consents,
        addConsent = True)


@login_required
@researcher_required
@blueprint.route('/survey/<int:id_survey>/consent/<int:id_consent>/delete')
@belong_researcher('consent')
def deleteConsent(id_survey,id_consent):
    consent = Consent.query.get(id_consent)
    db.session.delete(consent)
    db.session.commit()
    flash('consent removed')
    return redirect(url_for('researcher.addConsent',id_survey = id_survey))

@login_required
@researcher_required
@blueprint.route('/survey/<int:id_survey>/consent/<int:id_consent>', methods = ['GET', 'POST'])
@belong_researcher('consent')
def editConsents(id_survey, id_consent):
    consent = Consent.query.get(id_consent)
    form = EditConsentForm()
    if form.validate_on_submit():
        consent.text = form.text.data
        db.session.add(consent)
        db.session.commit()
        flash('Edited consent')
        return redirect(url_for('researcher.addConsent',id_survey = id_survey))
    elif request.method != "POST":
        form.text.data = consent.text
        consents = Consent.query.filter(Consent.survey_id == id_survey)
    return render_template('/researcher/consents.html',
        title = "consent",
        form = form,
        id_survey = id_survey,
        consents = consents,
        editConsent = True)


@login_required
@researcher_required
@blueprint.route('/survey/<int:id_survey>/section/new', methods = ['GET', 'POST'])
@belong_researcher('survey')
def addSection(id_survey):
    survey = Survey.query.get(id_survey)
    form = SectionForm()
    if form.validate_on_submit():
        section = Section(title = form.title.data,
            description = form.description.data,
            sequence = form.sequence.data,
            percent = form.percent.data,
            survey = survey
            )
        db.session.add(section)
        db.session.commit()
        flash('Adding section.')
        return redirect(url_for('researcher.editSurvey',id_survey = survey.id))
    # heuristics of the next sequence
    section = Section.query.filter(Section.survey_id==id_survey).order_by(Section.sequence.desc())
    if section.count()>=2 and section[0].sequence==section[1].sequence:
        # see the last and  penultimate
        form.sequence.data= section[0].sequence
    elif section.count()>=1:
        form.sequence.data= section[0].sequence + 1
    else:
        form.sequence.data =1
    return render_template('/researcher/addEditSection.html',
        title = "consent",
        form = form,
        survey = survey,
        sections = survey.sections.all(),
        #add = true, you is adding a new section
        addSection = True)


@login_required
@researcher_required
@blueprint.route('/survey/<int:id_survey>/section/<int:id_section>', methods = ['GET', 'POST'])
@belong_researcher('section')
def editSection(id_survey, id_section):
    section = Section.query.get(id_section)
    form = SectionForm()
    sections = Survey.query.get(id_survey).sections.all()
    if form.validate_on_submit():
        section.title = form.title.data
        section.description = form.description.data
        section.sequence = form.sequence.data
        section.percent = form.percent.data
        db.session.add(section)
        db.session.commit()
        flash('Save changes')
        return redirect(url_for('researcher.editSection',id_survey = id_survey, id_section = id_section))
    elif request.method != "POST":
        form.title.data = section.title
        form.description.data = section.description
        form.sequence.data = section.sequence
        form.percent.data = section.percent
    path=tips_path(section)
    return render_template('/researcher/addEditSection.html',
        title = "consent",
        form = form,
        survey = Survey.query.get(id_survey),
        sections = sections,
        editSection = True,
        id_section = id_section,
        path = path)


@login_required
@researcher_required
@blueprint.route('/survey/<int:id_survey>/deleteSection/<int:id_section>')
@belong_researcher('section')
def deleteSection(id_survey,id_section):
    section = Section.query.get(id_section)
    db.session.delete(section)
    db.session.commit()
    flash('Section removed')
    return redirect(url_for('researcher.editSurvey',id_survey = id_survey))

@login_required
@researcher_required
@blueprint.route('/survey/<int:id_survey>/deleteSection/<int:id_section>')
@belong_researcher('section')
def duplicate_section(id_survey,id_section):
    def _duplicate_question(s,q):
        pass

    def _duplicate_section(s_parent,section):
        section_cp = Section(title= section.title, description=section.description,\
                sequence=section.sequence, percent=section.percent,\
                parent= s_parent)

        db.session.add(section_cp)
        for s in section.children:
            _duplicate_section(section_cp,s)


    section = Section.query.get(id_section)
    section_cp = Section(title= section.title, description=section.description,\
            sequence=section.sequence, percent=section.percent,\
            parent= section.parent, suvey=section.survey)
    db.session.add(section_cp)
    for question in section.questions:
       _duplicate_question(section_cp,question)
    for s in section.children:
        _duplicate_section(section_cp,s)
    db.session.commit()
    flash('Section duplicated')
    return redirect(url_for('researcher.editSurvey',id_survey = id_survey))   


@login_required
@researcher_required
@blueprint.route('/survey/<int:id_survey>/section/<int:id_section>/new', methods = ['GET', 'POST'])
@belong_researcher('section')
def addSubSection(id_survey, id_section):
    parentSection = Section.query.get(id_section)
    form = SectionForm()
    if form.validate_on_submit():
        section = Section(title = form.title.data,
            description = form.description.data,
            sequence = form.sequence.data,
            percent = form.percent.data,
            parent = parentSection)
        db.session.add(section)
        db.session.commit()
        flash('Adding subsection.')
        return redirect(url_for('researcher.editSection',id_survey = id_survey, id_section = id_section))
    # heuristics of the next sequence
    section = Section.query.filter(Section.parent_id==id_section).order_by(Section.sequence.desc())
    if section.count()>=2 and section[0].sequence==section[1].sequence:
        # see the last and  penultimate
        form.sequence.data= section[0].sequence
    elif section.count()>=1:
        form.sequence.data= section[0].sequence + 1
    else:
        form.sequence.data =1
    path=tips_path(parentSection)
    return render_template('/researcher/addEditSection.html',
        title = "consent",
        form = form,
        survey = Survey.query.get(id_survey),
        sections = Survey.query.get(id_survey).sections.all(),
        addSubSection = True,
        path = path)


def selectType(form):

    if form.questionType.data =='yn':
        question = QuestionYN()
    if form.questionType.data == 'numerical':
        question = QuestionNumerical()
    if form.questionType.data == 'text':
        question = QuestionText(isNumber=form.isNumber.data,
            regularExpression=form.regularExpression.data,
            errorMessage=form.errorMessage.data)
    if form.questionType.data == 'choice':
        l = [form.answer1.data,
        form.answer2.data,
        form.answer3.data,
        form.answer4.data,
        form.answer5.data,
        form.answer6.data,
        form.answer7.data,
        form.answer8.data,
        form.answer9.data]
        l_aux=[]
        for i in l:
            if len(i)!=0:
                l_aux.append(i)    
        question = QuestionChoice(choices = l_aux)
    if form.questionType.data == 'likertScale':
        question = QuestionLikertScale(minLikert=form.minLikert.data,
            maxLikert=form.maxLikert.data, labelMin=form.labelMinLikert.data,
            labelMax=form.labelMaxLikert.data)
    
    print (form.questionType.data)
    #decision:
    if form.decisionType.data !='none':
        question.is_real_money= form.is_real_money.data
    if form.decisionType.data == "part_two":
        l = [form.answer1.data,
        form.answer2.data]
        question.choices = l[0:2]
    if form.decisionType.data == "decision_five":
        l = [form.answer1.data]
        question.choices = l[0:1]

    question.decision=form.decisionType.data
    question.text = form.text.data
    question.required = form.required.data
    question.expectedAnswer = form.expectedAnswer.data
    question.maxNumberAttempt = form.maxNumberAttempt.data
    return question



@login_required
@researcher_required
@blueprint.route('/survey/<int:id_survey>/section/<int:id_section>/addQuestion', methods = ['GET', 'POST'])
@belong_researcher('section')
def addQuestion(id_survey, id_section):
    section = Section.query.get(id_section)
    form = QuestionForm()
    if form.validate_on_submit():
        question = selectType(form)
        question.section = section
        db.session.add(question)
        db.session.commit()
        flash('Adding question')
        return redirect(url_for('researcher.addQuestion',id_survey = id_survey, id_section = id_section))
    path=tips_path(section)
    return render_template('/researcher/addEditQuestion.html',
        title = "Question",
        form = form,
        survey = Survey.query.get(id_survey),
        sections = Survey.query.get(id_survey).sections.all(),
        section = section,
        questions = section.questions,
        addQuestion = True,
        question_type = form.questionType.data,
        decision_type = form.decisionType.data,
        path = path)


@login_required
@researcher_required
@blueprint.route('/survey/<int:id_survey>/section/<int:id_section>/question/<int:id_question>', methods = ['GET', 'POST'])
@belong_researcher('question')
def editQuestion(id_survey, id_section,id_question):
    question = Question.query.get(id_question)
    form = QuestionForm()    
    if form.validate_on_submit():
        q = selectType(form)
        q.id = question.id
        q.section = question.section
        db.session.delete (question)
        db.session.commit()
        db.session.add(q)
        db.session.commit()
        flash('Adding question')
        return redirect(url_for('researcher.addQuestion',id_survey = id_survey, id_section = id_section))
    elif request.method != "POST":
        form.text.data = question.text
        form.required.data = question.required
        form.expectedAnswer.data = question.expectedAnswer
        form.maxNumberAttempt.data = question.maxNumberAttempt
        form.is_real_money.data = question.is_real_money
        if isinstance(question, QuestionText):
            form.regularExpression.data = question.regularExpression
            form.isNumber.data = question.isNumber
            form.errorMessage.data = question.errorMessage
        if isinstance (question,QuestionChoice):
            l= question.choices
            if len(l) >0:
                form.answer1.data = l[0]
            if len(l) >1:
                form.answer2.data = l[1]
            if len(l) >2:
                form.answer3.data = l[2]
            if len(l) >3:
                form.answer4.data = l[3]
            if len(l) >4:
                form.answer5.data = l[4]
            if len(l) >5:
                form.answer6.data = l[5]
            if len(l) >6:
                form.answer7.data = l[6]
            if len(l) >7:
                form.answer8.data = l[7]
            if len(l) >8:
                form.answer9.data = l[8]
        if isinstance(question, QuestionLikertScale):
            form.labelMinLikert.data=question.labelMin
            form.labelMaxLikert.data=question.labelMax
        if question.decision=="decision_five":
            form.answer1.data = question.choices[0]
    section =  Section.query.get(id_section)
    path=tips_path(section)
    return render_template('/researcher/addEditQuestion.html',
        title = "Question",
        form = form,
        survey = Survey.query.get(id_survey),
        sections = Survey.query.get(id_survey).sections.all(),
        section = section,
        questions = Section.query.get(id_section).questions,
        editQuestion = True,
        question_type = question.type,
        decision_type = question.decision,
        path = path)

@login_required
@researcher_required
@blueprint.route('/survey/<int:id_survey>/Section/<int:id_section>/deleteQuestion/<int:id_question>')
@belong_researcher('question')
def deleteQuestion(id_survey,id_section,id_question):
        #
        #CUANDO TENGA SUBSECCIONES Y ENCUESTAR, EL ELIMINAR NO ES TRIVIAL
        #
    question = Question.query.get(id_question)
    db.session.delete(question)
    db.session.commit()
    flash('Question removed')
    return redirect(url_for('researcher.addQuestion',id_survey = id_survey, id_section=id_section))

@login_required
@researcher_required
@blueprint.route('/survey/exportStats/<int:id_survey>')
@belong_researcher('survey')
def export_stats(id_survey):
    '''Export stats in csv
    '''
    def export_users(writer):
        writer.writerow(['USERS:'])
        writer.writerow(['ID_USER', 'IP', 'STATE', 'START DATE', 'FINISH DATE'])
        sss = StateSurvey.query.filter(StateSurvey.survey_id==id_survey)
        for ss in sss:
            l=[ss.user_id, ss.ip, ss.get_status(), ss.start_date, ss.endDate]
            writer.writerow(l)

    def export_section(writer):
    
        def _export_section(section,writer):
            if section.children.count()!=0:
                for s in section.children:
                    l=[s.id, s.title, s.parent.id , s.sequence, s.percent]
                    writer.writerow(l)
                    _export_section(s,writer)

        writer.writerow(['SECTION:'])
        writer.writerow(['ID_SECTION','TITLE','SECTION_PARENT','SEQUENCE','PERCENT'])
        sections = Section.query.filter(Section.survey_id==id_survey).order_by(Section.sequence)
        for s in sections:
            l=[s.id,s.title,"None",s.sequence,s.percent]
            writer.writerow(l)
            _export_section(s,writer)

    def export_section_user(writer):
        writer.writerow(['USER/SECTION (ORDER BY SEQUENCE OF USER):'])
        writer.writerow(['USER_ID', 'SECTION_ID', 'TIME'])
        sss = StateSurvey.query.filter(StateSurvey.survey_id==id_survey)
        for ss in sss:
            for s in ss.sectionTime:
                l=[ss.user_id, s[0],s[1]]
                writer.writerow(l)

    def export_section_question(writer):
        def _export_section_question(section,writer):
            questions = section.questions
            for q in questions:
                l=[section.id, q.id,q.text,q.type, q.choices]
                writer.writerow(l)
            for s in section.children:
                _export_section_question(s,writer)

        writer.writerow(['SECTION/QUESTION:'])
        writer.writerow(['SECTION', 'ID_QUESTION', 'QUESTION', 'CHOICES'])
        sections = Section.query.filter(Section.survey_id==id_survey).order_by(Section.sequence)
        for s in sections:
            _export_section_question(s,writer)

    def export_question_user(writer):
        def _export_question_user(section,writer):
            answers = Answer.query.filter(Answer.question_id==Question.id,\
                Question.section_id==section.id)
            for ans in answers:
                if isinstance (ans.question,QuestionYN):
                    text = ans.answerYN
                if isinstance (ans.question,QuestionNumerical):
                    text = ans.answerNumeric
                if isinstance (ans.question,QuestionText):
                    text = ans.answerText
                if isinstance (ans.question,QuestionChoice):
                    text = ans.question.choices[ans.answerNumeric]
                if isinstance (ans.question, QuestionLikertScale):
                    text = ans.answerNumeric
                l=[ans.question_id,ans.question.section_id,ans.user_id,text,
                ans.differentialTime,ans.globalTime ]
                writer.writerow(l)
            for s in section.children:
                _export_question_user(s,writer)

        writer.writerow(['QUESTION/USER:'])
        writer.writerow(['ID_QUESTION','ID_SECTION','ID_USER', 'ANSWER', 'DIFFERENTIAL TIME',\
            'GLOBAL TIME','QUESTION'])
        sections = Section.query.filter(Section.survey_id==id_survey).order_by(Section.sequence)
        for s in sections:
            _export_question_user(s,writer)

    survey = Survey.query.get(id_survey)
    # ofile = tempfile.NamedTemporaryFile()
    ofile  = open('test.csv', "wb")
    writer = csv.writer(ofile, delimiter='\t', quotechar='"', quoting=csv.QUOTE_ALL)
    export_users(writer)
    export_section(writer)
    export_section_user(writer)
    export_section_question(writer)
    export_question_user(writer)
    l=["jaja"]
    writer.writerow(l)
    # ofile.close()
    flash ("Export stats")
    # return send_file(ofile, as_attachment=True, attachment_filename="stats_"+survey.title+'.csv')
    return redirect(url_for('researcher.index'))