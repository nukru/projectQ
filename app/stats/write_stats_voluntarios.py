from ..models import StateSurvey, Answer, Question
from app import db, stats_csv
import os
import csv
from app.decorators import async
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import case

# write stats of survey "como son nuestos voluntarios" according to the indications of researchers
# identifier blocks the questions of the first part
FIRST_PART=[5,6,7,8,9]
#identifier blocks the questions of the first part
LAST_PART=[14,15]
@async    
def write_stats(id_survey):
    f1 = open(os.path.join(stats_csv, str(id_survey)+".csv"),"w")
    writer = csv.writer(f1, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
    write_header(writer, id_survey)
    for  ss in StateSurvey.query.filter(StateSurvey.survey_id==1,StateSurvey.status.op('&')(StateSurvey.FINISH_OK)):
        write_answers(writer, ss.user_id)
        print ss.user_id
    print "done"

    f1.close()


def write_header(writer,id_survey):
    def header_time(s,l):
        l.append(s)
        l.append("global time")
        l.append("dif time")

    def header_range(s1,s2,i,j,l):
        l.append(s1)
        for k in range(i,j+1):
            header_time(s2+str(k), l)

    l=[]
    l.append("USER")
    l.append("IP")
    l.append("START DATE")
    l.append("FINISH DATE")
    l.append("STATUS")
    l.append("PART2")
    l.append("PART3")
    l.append("SEQUENCE")
    l.append("PART1,BLOQUE1")
    header_time("parte1b1p1",l)
    header_time("parte1b1p2",l)
    header_time("parte1b1p3",l)
    header_time("parte1b1p4",l)
    header_time("parte1b1p5",l)
    header_time("parte1b1p5.1",l)
    header_time("parte1b1p6",l)
    header_time("parte1b1p7",l)
    header_time("parte1b1p7.1",l)
    header_time("parte1b1p7.2",l)
    header_time("parte1b1p7.3",l)
    header_time("parte1b1p8",l)
    header_time("parte1b1p9",l)
    header_time("parte1b1p10",l)
    header_time("parte1b1p10.1",l)
    header_time("parte1b1p10.2",l)
    header_time("parte1b1p11",l)
    header_time("parte1b1p11.1",l)
    header_time("parte1b1p11.2",l)
    header_time("parte1b1p12",l)
    header_time("parte1b1p13",l)
    header_time("parte1b1p13.1",l)
    header_time("parte1b1p14",l)
    header_time("parte1b1p15",l)
    header_time("parte1b1p15.1",l)
    header_time("parte1b1p15.2",l)
    header_time("parte1b1p15.3",l)
    header_time("parte1b1p16",l)
    header_time("parte1b1p16.1",l)
    header_time("parte1b1p16.2",l)
    header_time("parte1b1p17",l)
    header_range("PART1,BLOQUE2","parte1b2p",18,34,l)
    header_range("PART1,BLOQUE3","parte1b3p",35,39,l)
    header_range("PART1,BLOQUE4","parte1b4p",40,44,l)
    header_range("PART1,BLOQUE5","parte1b5p",45,47,l)
    header_range("PART2,BLOQUE1","parte2b1p",1,10,l)
    header_range("PART2,BLOQUE1","parte2b2p",1,10,l)
    header_range("PART3,DEC1,V1,B1","parte3d1v1b1p",1,4,l)
    header_range("PART3,DEC1,V1,B2","parte3d1v1b2p",1,1,l)
    header_range("PART3,DEC1,V1,B3","parte3d1v1b3p",1,7,l)
    header_range("PART3,DEC1,V2,B1","parte3d1v2b1p",1,5,l)
    header_range("PART3,DEC1,V2,B2","parte3d1v2b2p",1,1,l)
    header_range("PART3,DEC1,V2,B3","parte3d1v2b3p",1,7,l)
    header_range("PART3,DEC2,B1","parte3d2b1p",1,3,l)
    header_range("PART3,DEC2,B2","parte3d2b2p",1,1,l)
    header_range("PART3,DEC2,B3","parte3d2b3p",1,7,l)
    header_range("PART3,DEC3,B1","parte3d3b1p",1,3,l)
    header_range("PART3,DEC3,B2","parte3d3b2p",1,1,l)
    header_range("PART3,DEC3,B3","parte3d3b3p",1,7,l)
    header_range("PART3,DEC4","parte3d4p",1,1,l)
    header_range("PART3,DEC5","parte3d5p",1,11,l)
    header_range("PART3,DEC6","parte3d6p",1,1,l)
    header_range("PART4,BLOQUE1","parte4B1p",1,1,l)
    header_range("PART4,BLOQUE2","parte4B2p",1,1,l)

    writer.writerow(l)



def write_answers(writer,user_id):
    def status(status):
        if status & StateSurvey.FINISH_OK:
            return "finish ok"
        if status & StateSurvey.TIMED_OUT:
            return "out of time"
        if status & StateSurvey.END_DATE_OUT:
            return "out of date"
        return "not finish"

    def part2(ss):
        PARTE2=10 # SECTION PARTE2 MONEY REAL
        if PARTE2 in ss.sequence:
            return "real money"
        else:
            return "untrue money"

    def part3(ss):
        PARTE3=12
        if PARTE3 in ss.sequence:
            return "real money"
        else:
            return "untrue money"

    def sequence(sequence):
        '''return sequence of dedicions
        '''        
        PART2_B1=[16,18]
        PART2_B2=[17,19]
        DEC1_V1=[40,52]
        DEC1_V2=[43,55]
        DEC2=[46,58]
        DEC3=[49,61]
        DEC4=[32,38]
        DEC5=[33,39]
        DEC6=[23,27]

        l=[]
        l.append((sequence.index(16) if 16 in sequence else sequence.index(18),"part2b1"))
        l.append((sequence.index(17) if 17 in sequence else sequence.index(19),"part2b2"))
        if 40 in sequence:
            l.append((sequence.index(40),"dec1v1"))
        elif 52 in sequence:
            l.append((sequence.index(52),"dec1v1"))
        elif 43 in sequence:
            l.append((sequence.index(43),"dec1v2"))
        elif 55 in sequence:
            l.append((sequence.index(55),"dec1v2"))
        l.append((sequence.index(46) if 46 in sequence else sequence.index(58),"dec2"))
        l.append((sequence.index(49) if 49 in sequence else sequence.index(61),"dec3"))
        l.append((sequence.index(32) if 32 in sequence else sequence.index(38),"dec4"))
        l.append((sequence.index(33) if 33 in sequence else sequence.index(39),"dec5"))
        l.append((sequence.index(23) if 23 in sequence else sequence.index(27),"dec6"))
        l.sort(cmp=lambda a,b: cmp(a[0],b[0]))
        l1 = [i[1] for i in l]
        return ', '.join(l1)



    A = [5]

    PARTE2=10 # SECTION PARTE2 MONEY REAL
    PARTE3=12 # SECTION PARTE 3 MONEY REAL

    SECTIONS_PARTE2REAL=[16,17]
    SECTIONS_PARTE2UNTRUE=[18,19]

    SECTIONS_PARTE3REAL=[40,41,42,43,44,45,46,47,48,49,50,51,32,33,23]
    SECTIONS_PARTE3UNTRUE=[52,53,54,55,56,57,58,59,60,61,62,63,38,39,27]
    
    SECTIONS_OTHER=[6,7,8,9,14,15]

    l=[]


    ss = StateSurvey.query.filter(StateSurvey.survey_id==1,
        StateSurvey.user_id==user_id).first()


    list_sections = A[:]
    if PARTE2 in ss.sequence:
        list_sections = list_sections+SECTIONS_PARTE2REAL
    else:
        list_sections=list_sections+SECTIONS_PARTE2UNTRUE

    if PARTE3 in ss.sequence:
        list_sections=list_sections+SECTIONS_PARTE3REAL
    else:
        list_sections=list_sections+SECTIONS_PARTE3UNTRUE

    list_sections=list_sections+SECTIONS_OTHER

    stmt1 = db.session.query(Question).\
        filter(Question.section_id.in_(list_sections)).subquery()
    question1= aliased(Question, stmt1)
    stmt2 = db.session.query(Answer).filter(Answer.user_id==user_id).subquery()
    answer1= aliased(Answer, stmt2)
    res = db.session.query(question1, answer1).\
        outerjoin(answer1, question1.id == answer1.question_id).order_by(case((
            (question1.section_id ==5,1),
            (question1.section_id ==6,2),
            (question1.section_id ==7,3),
            (question1.section_id ==8,4),
            (question1.section_id ==9,5),
            (question1.section_id ==16,6),
            (question1.section_id ==17,7),
            (question1.section_id ==18,8),
            (question1.section_id ==19,9),
            (question1.section_id ==40,10),
            (question1.section_id ==41,11),
            (question1.section_id ==42,12),
            (question1.section_id ==43,13),
            (question1.section_id ==44,14),
            (question1.section_id ==45,15),
            (question1.section_id ==52,16),
            (question1.section_id ==53,17),
            (question1.section_id ==54,18),
            (question1.section_id ==55,19),
            (question1.section_id ==56,20),
            (question1.section_id ==57,21),
            (question1.section_id ==46,22),
            (question1.section_id ==47,23),
            (question1.section_id ==48,24),
            (question1.section_id ==58,25),
            (question1.section_id ==59,26),
            (question1.section_id ==60,27),
            (question1.section_id ==49,28),
            (question1.section_id ==50,29),
            (question1.section_id ==51,30),
            (question1.section_id ==61,31),
            (question1.section_id ==62,32),
            (question1.section_id ==63,33),
            (question1.section_id ==32,34),
            (question1.section_id ==38,35),
            (question1.section_id ==33,36),
            (question1.section_id ==39,37),
            (question1.section_id ==23,38),
            (question1.section_id ==27,39),
            (question1.section_id ==14,40),
            (question1.section_id ==15,40))),question1.position)


    l.append(ss.user_id)
    l.append(ss.ip)
    l.append(ss.start_date)
    l.append(ss.endDate)
    l.append(status(ss.status))
    l.append(part2(ss))
    l.append(part3(ss))
    l.append(sequence(ss.sequence))

    section = res[0][0].section_id
    l.append(ss.sectionTime.get(section))
    for i in res:
        if i[0].section_id!=section:
            section = i[0].section_id
            l.append(ss.sectionTime.get(section))

        if i[1] is None:
            l.append("")
            l.append("")
            l.append("")
        else:
            ans = i[1]
            l.append(ans.answerText)
            l.append(ans.globalTime)
            l.append(ans.differentialTime)

    writer.writerow(l)