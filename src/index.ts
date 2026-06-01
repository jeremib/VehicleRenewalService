import { Container } from "@cloudflare/containers";

export class VehicleRenewalContainer extends Container {
  defaultPort = 80;
  sleepAfter = "5m";

  override onStart(): void {
    console.log("Vehicle renewal container started");
  }

  override onStop(): void {
    console.log("Vehicle renewal container stopped");
  }

  override onError(error: unknown): void {
    console.error("Container error:", error);
  }
}

export default {
  async fetch(request: Request, env: any): Promise<Response> {
    const container = env.VEHICLE_RENEWAL.getByName("default");
    return await container.fetch(request);
  },
};
