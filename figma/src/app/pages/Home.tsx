import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { ArrowRight, Users, Briefcase, Star, Search } from "lucide-react";
import { ImageWithFallback } from "../components/figma/ImageWithFallback";
import { api } from "../lib/api";

export function Home() {
  const [stats, setStats] = useState([
    { label: "Проектов в каталоге", value: "—" },
    { label: "Открытых позиций", value: "—" },
    { label: "Уникальных тегов", value: "—" },
  ]);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const [projectsResponse, positionsResponse] = await Promise.all([
          api.getProjects({ page: 1, page_size: 100 }),
          api.getPositions({ page: 1, page_size: 100, is_open: true }),
        ]);

        const projects = Array.isArray(projectsResponse?.items)
          ? projectsResponse.items
          : Array.isArray(projectsResponse)
            ? projectsResponse
            : [];

        const positions = Array.isArray(positionsResponse?.items)
          ? positionsResponse.items
          : Array.isArray(positionsResponse)
            ? positionsResponse
            : [];

        const tagCount = new Set(
          projects.flatMap((project: any) =>
            Array.isArray(project?.tags) ? project.tags : []
          )
        ).size;

        setStats([
          { label: "Проектов в каталоге", value: String(projects.length) },
          { label: "Открытых позиций", value: String(positions.length) },
          { label: "Уникальных тегов", value: String(tagCount) },
        ]);
      } catch (error) {
        console.error("Failed to load homepage stats:", error);
      }
    };

    void loadStats();
  }, []);

  const features = [
    {
      icon: Search,
      title: "Найдите проект мечты",
      description: "Актуальные проекты из API доступны без подмешивания демо-данных.",
    },
    {
      icon: Users,
      title: "Соберите команду",
      description: "Находите специалистов, управляйте ролями и приглашайте участников в проект.",
    },
    {
      icon: Star,
      title: "Растите профессионально",
      description: "Откликайтесь на реальные позиции и общайтесь с командами в одном интерфейсе.",
    },
  ];

  return (
    <div>
      <section className="relative overflow-hidden py-20 md:py-32">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/5" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-foreground mb-6 leading-tight">
                Находите проекты и создавайте будущее
              </h1>
              <p className="text-lg text-muted-foreground mb-8">
                ИнКоллаб — платформа для совместной работы над проектами. Находите единомышленников,
                создавайте команды и воплощайте идеи в жизнь.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  to="/projects"
                  className="inline-flex items-center justify-center px-6 py-3 bg-primary text-white rounded-lg hover:bg-accent transition-colors space-x-2"
                >
                  <span>Найти проект</span>
                  <ArrowRight className="w-5 h-5" />
                </Link>
                <Link
                  to="/projects/create"
                  className="inline-flex items-center justify-center px-6 py-3 border-2 border-primary text-primary rounded-lg hover:bg-secondary transition-colors"
                >
                  Создать проект
                </Link>
              </div>
            </div>
            <div className="relative">
              <div className="aspect-square rounded-2xl overflow-hidden shadow-2xl">
                <ImageWithFallback
                  src="https://images.unsplash.com/photo-1521737604893-d14cc237f11d?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx0ZWFtJTIwd29ya2luZyUyMHRvZ2V0aGVyfGVufDF8fHx8MTc3NTQ5MDcyOXww&ixlib=rb-4.1.0&q=80&w=1080"
                  alt="Team collaboration"
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="absolute -bottom-6 -left-6 w-32 h-32 bg-primary/10 rounded-full blur-3xl" />
              <div className="absolute -top-6 -right-6 w-32 h-32 bg-accent/10 rounded-full blur-3xl" />
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-4xl md:text-5xl font-bold text-primary mb-2">
                  {stat.value}
                </div>
                <div className="text-muted-foreground">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Почему выбирают ИнКоллаб?
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Мы создали платформу, которая помогает талантливым людям находить друг друга
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div
                  key={index}
                  className="bg-white rounded-xl p-8 shadow-sm border border-border hover:shadow-md transition-shadow"
                >
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <Icon className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="py-20 bg-gradient-to-r from-primary to-accent">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Готовы начать свой проект?
          </h2>
          <p className="text-lg text-white/90 mb-8">
            Присоединяйтесь к сообществу профессионалов и воплотите свои идеи в жизнь
          </p>
          <Link
            to="/projects/create"
            className="inline-flex items-center justify-center px-8 py-4 bg-white text-primary rounded-lg hover:bg-gray-100 transition-colors space-x-2 font-semibold"
          >
            <span>Создать проект</span>
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>
    </div>
  );
}
