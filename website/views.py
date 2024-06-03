from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from website.models import db, User, Course, ProgramOutcome, LearningOutcome

views = Blueprint('views', __name__)


@views.route('/')
def index():
    return render_template('index.html')


@views.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        tc_no = request.form.get('tc_no')
        password = request.form.get('password')

        if not tc_no or not password:
            flash('TC kimlik numarası ve parola gereklidir.')
            return render_template('login.html')

        user = User.query.filter_by(tc_no=tc_no).first()
        admin_exists = User.query.filter_by(role='admin').first() is not None

        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('views.admin_dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('views.teacher_dashboard'))
        elif not admin_exists and tc_no == "admin" and password == "admin":
            # Create a new admin user in the database
            hashed_password = generate_password_hash("admin", method="pbkdf2:sha256")
            new_admin = User(tc_no="admin", password=hashed_password, role="admin")
            db.session.add(new_admin)
            db.session.commit()
            login_user(new_admin)
            return redirect(url_for('views.admin_dashboard'))
        else:
            flash('Giriş başarısız. TC kimlik numarası veya parola hatalı.')
    return render_template('login.html')


@views.route('/course/<int:course_id>')
def course_details(course_id):
    course = Course.query.get_or_404(course_id)
    teacher = User.query.get(course.teacher_id)
    program_outcomes = ProgramOutcome.query.filter_by(department=course.department).all()
    learning_outcomes = LearningOutcome.query.filter_by(course_id=course_id).all()

    return render_template('course_details.html',
                           course_title=course.name,
                           faculty_name=course.department,
                           program_outcomes=[po.description for po in program_outcomes],
                           learning_outcomes=[{'week': lo.week, 'description': lo.description} for lo in learning_outcomes])


@views.route('/admin/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        return redirect(url_for('views.index'))

    if request.method == 'POST':
        tc_no = request.form.get('tc_no')
        password = request.form.get('password')
        role = request.form.get('role')

        if not tc_no or not password or not role:
            flash('Tüm alanlar doldurulmalıdır.')
        elif User.query.filter_by(tc_no=tc_no).first():
            flash('Bu TC kimlik numarası zaten kullanılıyor.')
        else:
            hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
            new_user = User(tc_no=tc_no, password=hashed_password, role=role)
            db.session.add(new_user)
            db.session.commit()
            flash('Yeni kullanıcı başarıyla eklendi.')
            return redirect(url_for('views.admin_dashboard'))

    return render_template('add_user.html')


@views.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.index'))


@views.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('views.index'))
    teachers = User.query.filter_by(role='teacher').all()
    courses = Course.query.all()
    program_outcomes = ProgramOutcome.query.all()
    users = User.query.all()  # Fetch all users
    return render_template('admin_dashboard.html', teachers=teachers, courses=courses,
                           program_outcomes=program_outcomes, users=users)


@views.route('/teacher_dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        return redirect(url_for('views.index'))
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    return render_template('teacher_dashboard.html', courses=courses)


@views.route('/admin/add_course', methods=['POST'])
@login_required
def add_course():
    course_name = request.form.get('course_name')
    course_content = request.form.get('course_content')
    department = request.form.get('department')

    if not course_name or not department:
        flash('Lütfen gerekli alanları doldurun.')
        return redirect(url_for('views.add_course'))

    new_course = Course(name=course_name, content=course_content, department=department)
    db.session.add(new_course)
    db.session.commit()

    flash('Ders başarıyla eklendi.')
    return redirect(url_for('views.admin_dashboard'))


@views.route('/admin/assign_teacher', methods=['POST'])
@login_required
def assign_teacher():
    if current_user.role != 'admin':
        return redirect(url_for('views.index'))
    course_id = request.form.get('course_id')
    teacher_id = request.form.get('teacher_id')
    course = Course.query.get(course_id)
    teacher_courses_count = Course.query.filter_by(teacher_id=teacher_id).count()
    if teacher_courses_count < 6:
        course.teacher_id = teacher_id
        db.session.commit()
    else:
        flash('Bir öğretim elemanına en fazla 6 ders atanabilir.')
    return redirect(url_for('views.admin_dashboard'))


@views.route('/teacher/add_content/<int:course_id>', methods=['GET', 'POST'])
@login_required
def add_content(course_id):
    if current_user.role != 'teacher':
        return redirect(url_for('views.index'))
    course = Course.query.get(course_id)
    if request.method == 'POST':
        content = request.form.get('content')
        course.content = content
        db.session.commit()
        return redirect(url_for('views.teacher_dashboard'))
    return render_template('add_content.html', course=course)


@views.route('/teacher/add_learning_outcome/<int:course_id>', methods=['GET', 'POST'])
@login_required
def add_learning_outcome(course_id):
    if current_user.role != 'teacher':
        return redirect(url_for('views.index'))
    course = Course.query.get(course_id)
    if request.method == 'POST':
        week = request.form.get('week')
        description = request.form.get('description')
        relation_to_program_outcome = request.form.get('relation_to_program_outcome')
        new_outcome = LearningOutcome(course_id=course.id, week=week, description=description,
                                      relation_to_program_outcome=relation_to_program_outcome)
        db.session.add(new_outcome)
        db.session.commit()
        return redirect(url_for('views.teacher_dashboard'))
    return render_template('add_learning_outcome.html', course=course)


@views.route('/admin/add_program_outcome', methods=['POST'])
@login_required
def add_program_outcome():
    if current_user.role != 'admin':
        return redirect(url_for('views.index'))
    course_id = request.form.get('course_id')
    description = request.form.get('description')

    course = Course.query.get(course_id)
    new_program_outcome = ProgramOutcome(department=course.department, description=description)
    db.session.add(new_program_outcome)
    db.session.commit()

    flash('Program çıktısı başarıyla eklendi.')
    return redirect(url_for('views.admin_dashboard'))


@views.route('/admin/delete_course/<int:course_id>', methods=['DELETE'])
@login_required
def delete_course(course_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Yetkisiz erişim'}), 403
    course = Course.query.get(course_id)
    db.session.delete(course)
    db.session.commit()
    return jsonify({'success': 'Ders başarıyla silindi.'}), 200


@views.route('/admin/get_assigned_courses/<int:teacher_id>')
@login_required
def get_assigned_courses(teacher_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Yetkisiz erişim'}), 403
    courses = Course.query.filter_by(teacher_id=teacher_id).all()
    return jsonify({'courses': [{'id': course.id, 'name': course.name, 'department': course.department} for course in
                                courses]}), 200


@views.route('/admin/unassign_course/<int:course_id>/<int:teacher_id>', methods=['POST'])
@login_required
def unassign_course(course_id, teacher_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Yetkisiz erişim'}), 403
    course = Course.query.get(course_id)
    if course.teacher_id == teacher_id:
        course.teacher_id = None
        db.session.commit()
        return jsonify({'success': 'Ders öğretim elemanından başarıyla alındı.'}), 200
    else:
        return jsonify({'error': 'Ders bu öğretim elemanına atanmış değil.'}), 400


@views.route('/admin/delete_user/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Yetkisiz erişim'}), 403

    user = User.query.get(user_id)
    if user is None:
        return jsonify({'error': 'Kullanıcı bulunamadı.'}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': 'Kullanıcı başarıyla silindi.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Kullanıcı silinemedi.', 'details': str(e)}), 500


@views.route('/admin/change_password', methods=['POST'])
@login_required
def change_password():
    if current_user.role != 'admin':
        flash('Bu işlemi gerçekleştirmek için yetkiniz yok.')
        return redirect(url_for('views.admin_dashboard'))

    teacher_id = request.form.get('teacher_id')
    admin_password = request.form.get('admin_password')
    new_password = request.form.get('new_password')

    if not check_password_hash(current_user.password, admin_password):
        flash('Admin şifresi hatalı.')
        return redirect(url_for('views.admin_dashboard'))

    teacher = User.query.get(teacher_id)
    if teacher and teacher.role == 'teacher':
        teacher.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()
        flash('Şifre başarıyla değiştirildi.')
    else:
        flash('Öğretim elemanı bulunamadı.')

    return redirect(url_for('views.admin_dashboard'))
