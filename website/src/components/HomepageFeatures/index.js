import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Low-Cost, High-Accuracy',
    Svg: require('@site/static/img/low_cost.svg').default,
    description: (
      <>
        Delta6 utilizes affordable 3D-printed parts, standard springs, and magnetic encoders, achieving precise 6-DOF force sensing at a fraction of the traditional cost.
      </>
    ),
  },
  {
    title: '6-DOF Force and Torque Sensing',
    Svg: require('@site/static/img/force_sensing.svg').default,
    description: (
      <>
        By leveraging a Delta-style parallel mechanism with antagonistic spring units, Delta6 captures forces and torques along all six axes, enabling detailed robotic interaction analysis.
      </>
    ),
  },
  {
    title: 'Flexible and Robust Design',
    Svg: require('@site/static/img/flexible_design.svg').default,
    description: (
      <>
        The compliant structure of Delta6 provides resilience to external impacts, making it ideal for collaborative robotics, human-robot interaction, and dynamic task environments.
      </>
    ),
  },
];

function Feature({Svg, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
