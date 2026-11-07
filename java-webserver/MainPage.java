public class MainPage {
    public static void main(String[] args) {
        System.out.println("🎨 Запуск красивого сайта...");
        try {
            WebServer.main(args);
        } catch (Exception e) {
            System.out.println("Ошибка: " + e.getMessage());
        }
    }
}