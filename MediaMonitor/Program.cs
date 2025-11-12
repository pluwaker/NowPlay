using System.Threading.Tasks;

namespace NowMediaMonitor
{
    internal class Program
    {
        static async Task Main(string[] args)
        {
            var monitor = new MediaMonitor();
            await monitor.Start();
        }
    }
}
