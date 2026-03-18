// Моковые данные для демонстрации
import { User, Project, Skill, Position, Application } from '../types';

export const SKILLS: Skill[] = [
  { id: '1', name: 'React', category: 'frontend' },
  { id: '2', name: 'TypeScript', category: 'frontend' },
  { id: '3', name: 'Node.js', category: 'backend' },
  { id: '4', name: 'Python', category: 'backend' },
  { id: '5', name: 'UI/UX Design', category: 'design' },
  { id: '6', name: 'Figma', category: 'design' },
  { id: '7', name: 'Project Management', category: 'management' },
  { id: '8', name: 'Data Analysis', category: 'data' },
  { id: '9', name: 'PostgreSQL', category: 'backend' },
  { id: '10', name: 'Docker', category: 'backend' },
  { id: '11', name: 'Vue.js', category: 'frontend' },
  { id: '12', name: 'Marketing', category: 'marketing' },
  { id: '13', name: 'GraphQL', category: 'backend' },
  { id: '14', name: 'Flutter', category: 'frontend' },
  { id: '15', name: 'Machine Learning', category: 'data' },
];

export const CURRENT_USER: User = {
  id: 'user-1',
  name: 'Александр Петров',
  email: 'alex@example.com',
  avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400',
  bio: 'Фронтенд-разработчик с опытом в React и TypeScript. Ищу интересные стартап-проекты.',
  skills: [SKILLS[0], SKILLS[1], SKILLS[2]],
  profileOpen: true,
  createdAt: '2024-01-15T10:00:00Z',
};

export const USERS: User[] = [
  CURRENT_USER,
  {
    id: 'user-2',
    name: 'Мария Смирнова',
    email: 'maria@example.com',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400',
    bio: 'UI/UX дизайнер, увлечена созданием интуитивных интерфейсов.',
    skills: [SKILLS[4], SKILLS[5]],
    profileOpen: true,
    createdAt: '2024-01-10T10:00:00Z',
  },
  {
    id: 'user-3',
    name: 'Дмитрий Иванов',
    email: 'dmitry@example.com',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400',
    bio: 'Backend-разработчик, специализируюсь на Python и Node.js.',
    skills: [SKILLS[3], SKILLS[2], SKILLS[8], SKILLS[9]],
    profileOpen: true,
    createdAt: '2024-02-01T10:00:00Z',
  },
  {
    id: 'user-4',
    name: 'Елена Волкова',
    email: 'elena@example.com',
    avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400',
    bio: 'Product Manager с опытом запуска стартапов.',
    skills: [SKILLS[6], SKILLS[11]],
    profileOpen: true,
    createdAt: '2024-01-20T10:00:00Z',
  },
  {
    id: 'user-5',
    name: 'Андрей Козлов',
    email: 'andrey@example.com',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400',
    bio: 'Data Scientist, работаю с ML и аналитикой данных.',
    skills: [SKILLS[7], SKILLS[14], SKILLS[3]],
    profileOpen: true,
    createdAt: '2024-02-05T10:00:00Z',
  },
];

export const MOCK_PROJECTS: Project[] = [
  {
    id: 'project-1',
    title: 'EcoTrack - Приложение для отслеживания углеродного следа',
    description: 'Мобильное приложение, которое помогает пользователям отслеживать и уменьшать свой углеродный след. Интегрируется с транспортными картами, анализирует покупки и предлагает экологичные альтернативы.',
    goals: 'Создать MVP за 3 месяца и запустить бета-тестирование среди студентов. Целевая аудитория - экологически осознанная молодежь 18-30 лет.',
    progress: 'Готов дизайн и прототип, начали разработку backend API. Ищем фронтенд-разработчика для мобильного приложения.',
    ownerId: 'user-2',
    owner: USERS[1],
    positions: [],
    participants: [],
    tags: ['Экология', 'Mobile', 'Стартап'],
    createdAt: '2024-02-10T10:00:00Z',
    updatedAt: '2024-02-15T10:00:00Z',
    status: 'active',
  },
  {
    id: 'project-2',
    title: 'StudyBuddy - Платформа для совместного обучения',
    description: 'Веб-платформа для создания учебных групп и совместного изучения материалов. Включает видеозвонки, общие доски для заметок, трекинг прогресса.',
    goals: 'Разработать функционал видео-комнат и системы gamification. Запуск в университетах в следующем семестре.',
    progress: 'Базовый функционал готов, работаем над видео-интеграцией и системой достижений.',
    ownerId: 'user-3',
    owner: USERS[2],
    positions: [],
    participants: [],
    tags: ['EdTech', 'Web', 'Collaboration'],
    createdAt: '2024-01-25T10:00:00Z',
    updatedAt: '2024-02-16T10:00:00Z',
    status: 'active',
  },
  {
    id: 'project-3',
    title: 'LocalMarket - Маркетплейс для локальных производителей',
    description: 'Платформа для прямых продаж от локальных фермеров и производителей потребителям. Минуя посредников, снижаем цены и поддерживаем местный бизнес.',
    goals: 'Запустить пилотный проект в 3 районах города, привлечь минимум 50 продавцов и 1000 покупателей.',
    progress: 'Разработан основной функционал, проведено тестирование. Нужна помощь с маркетингом и масштабированием.',
    ownerId: 'user-4',
    owner: USERS[3],
    positions: [],
    participants: [],
    tags: ['E-commerce', 'Социальный проект', 'Web'],
    createdAt: '2024-02-01T10:00:00Z',
    updatedAt: '2024-02-14T10:00:00Z',
    status: 'active',
  },
  {
    id: 'project-4',
    title: 'AI Resume Builder - Конструктор резюме с ИИ',
    description: 'Сервис для создания профессиональных резюме с помощью ИИ. Анализирует описание вакансии и помогает оптимизировать резюме под конкретную позицию.',
    goals: 'Интегрировать GPT-4 для анализа и генерации контента, создать библиотеку из 20+ шаблонов.',
    progress: 'Готова базовая версия с 5 шаблонами, работаем над интеграцией ИИ.',
    ownerId: 'user-1',
    owner: USERS[0],
    positions: [],
    participants: [],
    tags: ['AI', 'HR Tech', 'SaaS'],
    createdAt: '2024-02-08T10:00:00Z',
    updatedAt: '2024-02-17T10:00:00Z',
    status: 'active',
  },
];

// Позиции для проектов
export const MOCK_POSITIONS: Position[] = [
  {
    id: 'pos-1',
    projectId: 'project-1',
    title: 'Flutter-разработчик',
    description: 'Требуется опыт разработки мобильных приложений на Flutter. Будешь работать над UI компонентами и интеграцией с API.',
    requiredSkills: [SKILLS[13]],
    status: 'open',
    applications: [],
    createdAt: '2024-02-12T10:00:00Z',
  },
  {
    id: 'pos-2',
    projectId: 'project-2',
    title: 'UI/UX Дизайнер',
    description: 'Ищем дизайнера для доработки интерфейса и создания UI-kit. Опыт работы с Figma обязателен.',
    requiredSkills: [SKILLS[4], SKILLS[5]],
    status: 'open',
    applications: [],
    createdAt: '2024-02-13T10:00:00Z',
  },
  {
    id: 'pos-3',
    projectId: 'project-2',
    title: 'Frontend React Developer',
    description: 'Разработка новых фичей на React/TypeScript. Нужен опыт с WebRTC для видео-звонков.',
    requiredSkills: [SKILLS[0], SKILLS[1]],
    status: 'open',
    applications: [],
    createdAt: '2024-02-11T10:00:00Z',
  },
  {
    id: 'pos-4',
    projectId: 'project-3',
    title: 'Маркетолог',
    description: 'Нужен специалист для разработки маркетинговой стратегии и ведения соцсетей проекта.',
    requiredSkills: [SKILLS[11]],
    status: 'open',
    applications: [],
    createdAt: '2024-02-14T10:00:00Z',
  },
  {
    id: 'pos-5',
    projectId: 'project-4',
    title: 'ML Engineer',
    description: 'Работа с LLM для анализа резюме и вакансий. Опыт с prompt engineering и fine-tuning.',
    requiredSkills: [SKILLS[14], SKILLS[3]],
    status: 'open',
    applications: [],
    createdAt: '2024-02-15T10:00:00Z',
  },
  {
    id: 'pos-6',
    projectId: 'project-1',
    title: 'Backend Node.js Developer',
    description: 'Разработка REST API для мобильного приложения. Опыт с PostgreSQL и Docker.',
    requiredSkills: [SKILLS[2], SKILLS[8], SKILLS[9]],
    status: 'open',
    applications: [],
    createdAt: '2024-02-16T10:00:00Z',
  },
];

// Добавляем позиции к проектам
MOCK_PROJECTS[0].positions = [MOCK_POSITIONS[0], MOCK_POSITIONS[5]];
MOCK_PROJECTS[1].positions = [MOCK_POSITIONS[1], MOCK_POSITIONS[2]];
MOCK_PROJECTS[2].positions = [MOCK_POSITIONS[3]];
MOCK_PROJECTS[3].positions = [MOCK_POSITIONS[4]];

// Моковые отклики
export const MOCK_APPLICATIONS: Application[] = [
  {
    id: 'app-1',
    positionId: 'pos-3',
    userId: 'user-1',
    user: USERS[0],
    message: 'Привет! Я опытный React-разработчик с опытом работы с WebRTC. Буду рад присоединиться к вашему проекту!',
    status: 'pending',
    createdAt: '2024-02-16T10:00:00Z',
  },
];

MOCK_POSITIONS[2].applications = [MOCK_APPLICATIONS[0]];
